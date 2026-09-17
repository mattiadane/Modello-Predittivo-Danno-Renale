-- =============================================================================
-- CREAZIONE MATERIALIZED VIEW: CALCOLO DEGLI STADI AKI (KDIGO)
-- =============================================================================
-- Questa vista calcola lo stadio di Acute Kidney Injury (AKI) in modo dinamico
-- nel tempo per ogni paziente in ICU, combinando tre criteri KDIGO:
--   1. Volume dell'Output Urinario (UO)
--   2. Livelli di Creatinina sierica (Cr) e variazione rispetto al punto piu basso/Baseline
--   3. Eventi di Dialisi / Terapia Sostitutiva Renale (RRT)
-- =============================================================================

CREATE MATERIALIZED VIEW aki AS

WITH
-- -----------------------------------------------------------------------------
-- CTE 1: WEIGHT_DATA
-- Recupera il peso corporeo del paziente (in kg), necessario per calcolare
-- la diuresi oraria ponderata (mL/kg/h).
-- Cerca il peso primariamente da 'chartevents' (in kg); se assente, attinge da
-- 'omr' facendone la conversione da libbre (Lbs) a chilogrammi (0.45359237).
-- -----------------------------------------------------------------------------
weight_data AS (
    SELECT
        ie.stay_id,
        AVG(
            CASE
                -- Peso registrato direttamente in kg
                WHEN c.valuenum IS NOT NULL AND c.valuenum > 0 THEN c.valuenum
                -- Peso registrato in libbre (Lbs) convertito in Kg
                WHEN omr.result_value IS NOT NULL AND omr.result_value::DOUBLE PRECISION > 0
                    THEN omr.result_value::DOUBLE PRECISION * 0.45359237
                ELSE NULL
            END
        ) AS weight_kg
    FROM icustays ie
    LEFT JOIN chartevents c
        ON ie.stay_id = c.stay_id
        AND c.itemid IN (226512, 224639) -- ItemID MIMIC per il peso corporeo in kg
        AND c.valuenum > 0
    LEFT JOIN omr
        ON ie.subject_id = omr.subject_id
        AND omr.result_name = 'Weight (Lbs)'
    GROUP BY ie.stay_id
),

-- -----------------------------------------------------------------------------
-- CTE 2: UO_ORARIO
-- Estrae e somma le misurazioni dell'output urinario (mL) aggregate per ora
-- e per degenza (stay_id), scartando i pazienti senza un peso valido.
-- -----------------------------------------------------------------------------
uo_orario AS (
    SELECT
        oe.stay_id,
        oe.charttime,
        SUM(oe.value) AS urine_ml,
        w.weight_kg
    FROM outputevents oe
    JOIN weight_data w ON oe.stay_id = w.stay_id
    WHERE oe.itemid IN (
            226559, 226560, 226561, 226563, 226564,
            226565, 226567, 226557, 226558, 227488, 227489
          ) -- Tutti gli ItemID MIMIC per la produzione di urina (catetere, nefrostomia, ecc.)
      AND w.weight_kg > 0
    GROUP BY oe.stay_id, oe.charttime, w.weight_kg
),

-- -----------------------------------------------------------------------------
-- CTE 3: UO_WINDOWS
-- Calcola, per ogni timestamp, la somma progressiva delle urine (mL) e la
-- durata effettiva della finestra temporale (in ore) per 3 intervalli mobili:
--   - Ultime 6 ore (w6)
--   - Ultime 12 ore (w12)
--   - Ultime 24 ore (w24)
-- La durata effettiva (hours_Xh) viene calcolata tramite EXTRACT(EPOCH...) per
-- assicurarsi che la finestra copra davvero l'intervallo di ore richiesto.
-- -----------------------------------------------------------------------------
uo_windows AS (
    SELECT
        u.stay_id,
        u.charttime,
        u.weight_kg,
        -- Volumi cumulativi nelle finestre temporali
        SUM(u.urine_ml) OVER w6  AS uo_6h,
        SUM(u.urine_ml) OVER w12 AS uo_12h,
        SUM(u.urine_ml) OVER w24 AS uo_24h,
        -- Calcolo delle ore effettive di copertura della finestra temporale
        EXTRACT(EPOCH FROM (u.charttime - MIN(u.charttime) OVER w6)) / 3600.0  AS hours_6h,
        EXTRACT(EPOCH FROM (u.charttime - MIN(u.charttime) OVER w12)) / 3600.0 AS hours_12h,
        EXTRACT(EPOCH FROM (u.charttime - MIN(u.charttime) OVER w24)) / 3600.0 AS hours_24h
    FROM uo_orario u
    WINDOW
        w6  AS (PARTITION BY u.stay_id ORDER BY u.charttime RANGE BETWEEN '06:00:00'::INTERVAL PRECEDING AND CURRENT ROW),
        w12 AS (PARTITION BY u.stay_id ORDER BY u.charttime RANGE BETWEEN '12:00:00'::INTERVAL PRECEDING AND CURRENT ROW),
        w24 AS (PARTITION BY u.stay_id ORDER BY u.charttime RANGE BETWEEN '24:00:00'::INTERVAL PRECEDING AND CURRENT ROW)
),

-- -----------------------------------------------------------------------------
-- CTE 4: KDIGO_UO
-- Assegna lo stadio AKI (0, 1, 2 o 3) basandosi sui volumi urinari (mL/kg/h):
--   - Stadio 3: < 0.3 mL/kg/h per >= 24 ore OPPURE Anuria (0 mL) per >= 12 ore
--   - Stadio 2: < 0.5 mL/kg/h per >= 12 ore
--   - Stadio 1: < 0.5 mL/kg/h per >= 6 ore
-- -----------------------------------------------------------------------------
kdigo_uo AS (
    SELECT
        uw.stay_id,
        uw.charttime,
        CASE
            WHEN uw.hours_24h >= 24 AND (uw.uo_24h / (uw.weight_kg * 24.0)) < 0.3 THEN 3
            WHEN uw.hours_12h >= 12 AND uw.uo_12h = 0 THEN 3
            WHEN uw.hours_12h >= 12 AND (uw.uo_12h / (uw.weight_kg * 12.0)) < 0.5 THEN 2
            WHEN uw.hours_6h >= 6   AND (uw.uo_6h / (uw.weight_kg * 6.0)) < 0.5   THEN 1
            ELSE 0
        END AS aki_stage_uo
    FROM uo_windows uw
),

-- -----------------------------------------------------------------------------
-- CTE 5: RRT_EVENTS
-- Identifica se il paziente è sottoposto a Dialisi / Renal Replacement Therapy
-- durante la degenza. Qualsiasi evento RRT porta automaticamente lo stadio AKI a 3.
-- -----------------------------------------------------------------------------
rrt_events AS (
    SELECT DISTINCT
        ie.stay_id,
        ce.charttime
    FROM icustays ie
    JOIN chartevents ce
        ON ie.subject_id = ce.subject_id
        AND ce.charttime >= ie.intime
        AND ce.charttime <= ie.outtime
    WHERE ce.itemid IN (
            224146, 224149, 224150, 224151, 225802,
            225803, 225805, 225809, 225955, 225976, 225977
          ) -- ItemID relativi a procedure di emodialisi / CRRT
      AND ce.valuenum IS NOT NULL
      AND ce.valuenum > 0
),

-- -----------------------------------------------------------------------------
-- CTE 6: CR_PAZIENTE
-- Estrae tutte le misurazioni di laboratorio della Creatinina sierica (Item 50912).
-- Estende la ricerca fino a 365 giorni prima dell'ingresso in ICU per poter
-- calcolare una baseline storica accurata.
-- -----------------------------------------------------------------------------
cr_paziente AS (
    SELECT
        ie.stay_id,
        ie.hadm_id,
        ie.subject_id,
        ie.intime,
        l.charttime,
        l.valuenum AS creatina
    FROM icustays ie
    JOIN labevents l ON ie.subject_id = l.subject_id
    WHERE l.itemid = 50912 -- Creatinina sierica
      AND l.valuenum IS NOT NULL
      AND l.valuenum > 0
      AND l.charttime >= (ie.intime - INTERVAL '365 days')
      AND l.charttime <= ie.outtime
),

-- -----------------------------------------------------------------------------
-- CTE 7: CR_BASELINE
-- Determina il valore di riferimento (Baseline) della creatinina per ogni ricovero.
-- Applica una rigida gerarchia clinica tramite COALESCE:
--   1. Valore minimo tra 365 e 7 giorni prima dell'ingresso in ICU (preferito)
--   2. In mancanza, valore minimo nei 7 giorni prima dell'ingresso
--   3. In mancanza, il primo valore disponibile dopo l'ingresso in ICU
-- -----------------------------------------------------------------------------
cr_baseline AS (
    SELECT
        cp.stay_id,
        COALESCE(
            -- Priorità 1: Storico da 1 anno a 7 giorni prima
            MIN(CASE WHEN cp.charttime >= (cp.intime - INTERVAL '365 days') AND cp.charttime < (cp.intime - INTERVAL '7 days') THEN cp.creatina END),
            -- Priorità 2: Pre-ICU recente (ultimi 7 giorni)
            MIN(CASE WHEN cp.charttime >= (cp.intime - INTERVAL '7 days')   AND cp.charttime < cp.intime THEN cp.creatina END),
            -- Priorità 3: Valore post-ingresso in ICU
            MIN(CASE WHEN cp.charttime >= cp.intime THEN cp.creatina END)
        ) AS baseline_creatina
    FROM cr_paziente cp
    GROUP BY cp.stay_id
),

-- -----------------------------------------------------------------------------
-- CTE 8: KDIGO_CR
-- Stadiazione AKI basata sulle variazioni di Creatinina:
--   - Stadio 3: Cr >= 3.0x Baseline OR (Cr >= 4.0 mg/dL con aumento >= 0.3 rispetto al Nadir 48h)
--   - Stadio 2: Cr >= 2.0x Baseline
--   - Stadio 1: Cr >= 1.5x Baseline OR incremento assoluto >= 0.3 mg/dL rispetto al Nadir delle ultime 48h
-- -----------------------------------------------------------------------------
kdigo_cr AS (
    SELECT
        cp.stay_id,
        cp.charttime,
        cp.creatina,
        cb.baseline_creatina,
        CASE
            -- Stadio 3
            WHEN (cp.creatina / NULLIF(cb.baseline_creatina, 0)) >= 3.0
               OR (cp.creatina >= 4.0 AND (cp.creatina - MIN(cp.creatina) OVER w48) >= 0.3) THEN 3
            -- Stadio 2
            WHEN (cp.creatina / NULLIF(cb.baseline_creatina, 0)) >= 2.0 THEN 2
            -- Stadio 1
            WHEN (cp.creatina / NULLIF(cb.baseline_creatina, 0)) >= 1.5
               OR (cp.creatina - MIN(cp.creatina) OVER w48) >= 0.3 THEN 1
            ELSE 0
        END AS aki_stage_cr
    FROM cr_paziente cp
    JOIN cr_baseline cb ON cp.stay_id = cb.stay_id
    WHERE cp.charttime >= cp.intime
    -- Finestra mobile di 48 ore per il calcolo del Nadir (valore più basso)
    WINDOW w48 AS (PARTITION BY cp.stay_id ORDER BY cp.charttime RANGE BETWEEN '48:00:00'::INTERVAL PRECEDING AND CURRENT ROW)
),

-- -----------------------------------------------------------------------------
-- CTE 9: ALL_TIMESTAMPS
-- Crea la griglia temporale unificata che raccoglie tutti i timestamp in cui
-- è stata eseguita ALMENO UNA misurazione (Cr, UO o inizio RRT).
-- -----------------------------------------------------------------------------
all_timestamps AS (
    SELECT stay_id, charttime FROM kdigo_cr
    UNION
    SELECT stay_id, charttime FROM kdigo_uo
    UNION
    SELECT stay_id, charttime FROM rrt_events
),

-- -----------------------------------------------------------------------------
-- CTE 10: FF_CR (Forward-Fill per Creatinina)
-- Propaga l'ultimo stadio AKI calcolato per la Creatinina nei timestamp
-- intermedi in cui la Creatinina non è stata misurata (es. durante un log UO).
-- Utilizza la tecnica del "Grouping by COUNT" per la propagazione del valore.
-- -----------------------------------------------------------------------------
ff_cr AS (
    SELECT
        t.stay_id,
        t.charttime,
        MAX(t.aki_stage_cr) OVER (PARTITION BY t.stay_id, t.grp_cr) AS aki_stage_cr
    FROM (
        SELECT
            ts.stay_id,
            ts.charttime,
            c.aki_stage_cr,
            -- Crea un ID di gruppo che si incrementa ogni volta che incontriamo un nuovo valore non nullo
            COUNT(c.aki_stage_cr) OVER (PARTITION BY ts.stay_id ORDER BY ts.charttime ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS grp_cr
        FROM all_timestamps ts
        LEFT JOIN (
            SELECT stay_id, charttime, MAX(aki_stage_cr) AS aki_stage_cr
            FROM kdigo_cr
            GROUP BY stay_id, charttime
        ) c ON ts.stay_id = c.stay_id AND ts.charttime = c.charttime
    ) t
),

-- -----------------------------------------------------------------------------
-- CTE 11: FF_UO (Forward-Fill per Output Urinario)
-- Analogamente alla CTE 10, propaga l'ultimo stadio AKI calcolato dall'Output
-- Urinario lungo tutta la Timeline dei timestamp unificati.
-- -----------------------------------------------------------------------------
ff_uo AS (
    SELECT
        t.stay_id,
        t.charttime,
        MAX(t.aki_stage_uo) OVER (PARTITION BY t.stay_id, t.grp_uo) AS aki_stage_uo
    FROM (
        SELECT
            ts.stay_id,
            ts.charttime,
            u.aki_stage_uo,
            COUNT(u.aki_stage_uo) OVER (PARTITION BY ts.stay_id ORDER BY ts.charttime ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS grp_uo
        FROM all_timestamps ts
        LEFT JOIN (
            SELECT stay_id, charttime, MAX(aki_stage_uo) AS aki_stage_uo
            FROM kdigo_uo
            GROUP BY stay_id, charttime
        ) u ON ts.stay_id = u.stay_id AND ts.charttime = u.charttime
    ) t
)

-- =============================================================================
-- SELEZIONE FINALE
-- Combina i risultati propagati di Creatinina (ff_cr), Output Urinario (ff_uo)
-- e la presenza di RRT.
-- Lo stadio AKI finale (aki_stage) per ciascun timestamp è il valore MASSIMO
-- (GREATEST) tra i 3 criteri individuali.
-- =============================================================================
SELECT
    ie.subject_id,
    ie.hadm_id,
    ie.stay_id,
    ts.charttime,
    COALESCE(cr.aki_stage_cr, 0) AS aki_stage_cr,
    COALESCE(uo.aki_stage_uo, 0) AS aki_stage_uo,
    CASE
        WHEN rrt.stay_id IS NOT NULL THEN 1
        ELSE 0
    END AS aki_stage_rrt,
    -- Stadio KDIGO complessivo: il peggiore (massimo) raggiunto in quel momento
    GREATEST(
        COALESCE(cr.aki_stage_cr, 0),
        COALESCE(uo.aki_stage_uo, 0),
        CASE WHEN rrt.stay_id IS NOT NULL THEN 3 ELSE 0 END
    ) AS aki_stage
FROM all_timestamps ts
JOIN icustays ie ON ts.stay_id = ie.stay_id
LEFT JOIN ff_cr cr  ON ts.stay_id = cr.stay_id AND ts.charttime = cr.charttime
LEFT JOIN ff_uo uo  ON ts.stay_id = uo.stay_id AND ts.charttime = uo.charttime
LEFT JOIN rrt_events rrt ON ts.stay_id = rrt.stay_id AND ts.charttime >= rrt.charttime
ORDER BY ie.subject_id, ie.hadm_id, ie.stay_id, ts.charttime;

-- Indice di ottimizzazione per interrogazioni veloci basate sui timestamp del paziente
CREATE INDEX idx_aki_official
    ON aki (subject_id, hadm_id, stay_id, charttime);