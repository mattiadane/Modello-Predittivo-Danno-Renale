-- Creazione della vista materializzata per la stadiazione dell'Acute Kidney Injury (AKI) basata su criteri KDIGO
CREATE MATERIALIZED VIEW aki AS

--  Estrae tutti i valori di creatinina per ricovero, includendo lo storico fino a 365 giorni prima
WITH creatina_paziente AS (
    SELECT
        adm.subject_id,
        adm.hadm_id,
        p.gender,
        p.anchor_age,
        adm.admittime,
        l.charttime,
        l.valuenum AS creatina
    FROM admissions adm
    JOIN patients p ON adm.subject_id = p.subject_id
    JOIN labevents l ON adm.subject_id = l.subject_id
    WHERE l.itemid = 50912 -- Codice per la Creatinina sierica
      AND l.valuenum IS NOT NULL
      AND l.valuenum > 0::DOUBLE PRECISION
      AND l.charttime >= (adm.admittime - '365 days'::INTERVAL) -- Finestra temporale baseline
      AND l.charttime <= adm.dischtime
),

--  Calcola i valori minimi di creatinina in diverse finestre temporali pre e intra-ricovero
aggregati_baseline AS (
    SELECT
        creatina_paziente.hadm_id,
        creatina_paziente.subject_id,
        creatina_paziente.gender,
        creatina_paziente.anchor_age,
        -- Minima creatinina tra 1 anno e 7 giorni prima dell'ammissione
        MIN(CASE
            WHEN creatina_paziente.charttime >= (creatina_paziente.admittime - '365 days'::INTERVAL)
             AND creatina_paziente.charttime < (creatina_paziente.admittime - '7 days'::INTERVAL)
            THEN creatina_paziente.creatina
            ELSE NULL::DOUBLE PRECISION
        END) AS creat_pre_365_7d,
        -- Minima creatinina nei 7 giorni precedenti l'ammissione
        MIN(CASE
            WHEN creatina_paziente.charttime >= (creatina_paziente.admittime - '7 days'::INTERVAL)
             AND creatina_paziente.charttime < creatina_paziente.admittime
            THEN creatina_paziente.creatina
            ELSE NULL::DOUBLE PRECISION
        END) AS creat_pre_7d,
        -- Minima creatinina registrata durante il ricovero attuale
        MIN(CASE
            WHEN creatina_paziente.charttime >= creatina_paziente.admittime
            THEN creatina_paziente.creatina
            ELSE NULL::DOUBLE PRECISION
        END) AS creat_min_ricovero
    FROM creatina_paziente
    GROUP BY creatina_paziente.hadm_id, creatina_paziente.subject_id, creatina_paziente.gender, creatina_paziente.anchor_age
),

--  Stima la creatinina di base (MDRD se mancante) e seleziona il valore di baseline definitivo
final_baseline AS (
    SELECT
        b.hadm_id,
        b.subject_id,
        -- Formula MDRD inversa per stimare la creatinina baseline teorica assumendo eGFR = 75 mL/min/1.73m²
        GREATEST(ROUND((75.0 / (175.0 * POWER(GREATEST(b.anchor_age::INTEGER, 18)::NUMERIC, '-0.203'::NUMERIC) *
            CASE WHEN b.gender = 'F'::BPCHAR THEN 0.742 ELSE 1.0 END)) ^ ('-1'::INTEGER::NUMERIC / 1.154), 2), 0.1) AS creat_mdrd_stimata,
        -- Priorità di selezione della baseline: 1) Pre 365-7d, 2) Pre 7d, 3) Minima in ricovero, 4) MDRD stimata
        COALESCE(b.creat_pre_365_7d, b.creat_pre_7d, b.creat_min_ricovero,
            GREATEST(ROUND((75.0 / (175.0 * POWER(GREATEST(b.anchor_age::INTEGER, 18)::NUMERIC, '-0.203'::NUMERIC) *
            CASE WHEN b.gender = 'F'::BPCHAR THEN 0.742 ELSE 1.0 END)) ^ ('-1'::INTEGER::NUMERIC / 1.154), 2), 0.1)::DOUBLE PRECISION) AS baseline_definitiva
    FROM aggregati_baseline b
),

--  Associa la baseline e calcola il valore minimo (nadir) di creatinina nelle 48 ore precedenti
aki_creatina_raw AS (
    SELECT
        cp.subject_id,
        cp.hadm_id,
        cp.admittime,
        cp.charttime,
        cp.creatina,
        fb.baseline_definitiva,
        MIN(cp.creatina) OVER (PARTITION BY cp.hadm_id ORDER BY cp.charttime RANGE BETWEEN '48:00:00'::INTERVAL PRECEDING AND CURRENT ROW) AS nadir_48h
    FROM creatina_paziente cp
    JOIN final_baseline fb ON fb.hadm_id = cp.hadm_id
),

--  Calcola lo stadio AKI secondo la Creatinina (Criteri KDIGO)
aki_creatina AS (
    SELECT
        aki_creatina_raw.subject_id,
        aki_creatina_raw.hadm_id,
        aki_creatina_raw.charttime,
        CASE
            -- Stage 3: Creatinina >= 3x baseline OPPURE >= 4.0 mg/dL con un incremento acuto >= 0.3 mg/dL
            WHEN (aki_creatina_raw.creatina / NULLIF(aki_creatina_raw.baseline_definitiva, 0::DOUBLE PRECISION)) >= 3.0::DOUBLE PRECISION
              OR (aki_creatina_raw.creatina >= 4.0::DOUBLE PRECISION AND (aki_creatina_raw.creatina - aki_creatina_raw.nadir_48h) >= 0.3::DOUBLE PRECISION) THEN 3
            -- Stage 2: Creatinina tra 2.0x e 2.9x la baseline
            WHEN (aki_creatina_raw.creatina / NULLIF(aki_creatina_raw.baseline_definitiva, 0::DOUBLE PRECISION)) >= 2.0::DOUBLE PRECISION THEN 2
            -- Stage 1: Creatinina tra 1.5x e 1.9x la baseline OPPURE aumento >= 0.3 mg/dL nelle 48h
            WHEN (aki_creatina_raw.creatina / NULLIF(aki_creatina_raw.baseline_definitiva, 0::DOUBLE PRECISION)) >= 1.5::DOUBLE PRECISION
              OR (aki_creatina_raw.creatina - aki_creatina_raw.nadir_48h) >= 0.3::DOUBLE PRECISION THEN 1
            ELSE 0
        END AS stage_creatina
    FROM aki_creatina_raw
    WHERE aki_creatina_raw.charttime >= aki_creatina_raw.admittime
),

-- Calcola il peso medio in kg convertendolo da libbre (Lbs)
peso_pazienti AS (
    SELECT
        omr.subject_id,
        AVG(omr.result_value::DOUBLE PRECISION) * 0.45359237::DOUBLE PRECISION AS peso_kg
    FROM omr
    WHERE omr.result_name::TEXT = 'Weight (Lbs)'::TEXT
      AND omr.result_value::DOUBLE PRECISION > 0::DOUBLE PRECISION
    GROUP BY omr.subject_id
),

-- Aggrega l'output urinario orario per ricovero
diuresi_oraria AS (
    SELECT
        oe.subject_id,
        oe.hadm_id,
        oe.charttime,
        SUM(oe.value) AS urine_ml,
        w.peso_kg
    FROM outputevents oe
    JOIN peso_pazienti w ON oe.subject_id = w.subject_id
    WHERE w.peso_kg IS NOT NULL
      AND w.peso_kg > 0::DOUBLE PRECISION
      AND (oe.itemid = ANY (ARRAY[226559, 226560])) -- Item ID per la diuresi
    GROUP BY oe.subject_id, oe.hadm_id, oe.charttime, w.peso_kg
),

-- Calcola il volume di urina e le ore di copertura effettive per finestre mobili di 6h, 12h e 24h
diuresi_con_copertura AS (
    SELECT
        diuresi_oraria.subject_id,
        diuresi_oraria.hadm_id,
        diuresi_oraria.charttime,
        diuresi_oraria.peso_kg,
        SUM(diuresi_oraria.urine_ml) OVER w_6h AS urine_6h,
        SUM(diuresi_oraria.urine_ml) OVER w_12h AS urine_12h,
        SUM(diuresi_oraria.urine_ml) OVER w_24h AS urine_24h,
        DATE_PART('epoch'::TEXT, diuresi_oraria.charttime - MIN(diuresi_oraria.charttime) OVER w_6h) / 3600.0::DOUBLE PRECISION AS ore_coperte_6h,
        DATE_PART('epoch'::TEXT, diuresi_oraria.charttime - MIN(diuresi_oraria.charttime) OVER w_12h) / 3600.0::DOUBLE PRECISION AS ore_coperte_12h,
        DATE_PART('epoch'::TEXT, diuresi_oraria.charttime - MIN(diuresi_oraria.charttime) OVER w_24h) / 3600.0::DOUBLE PRECISION AS ore_coperte_24h
    FROM diuresi_oraria
    WINDOW w_6h AS (PARTITION BY diuresi_oraria.hadm_id ORDER BY diuresi_oraria.charttime RANGE BETWEEN '06:00:00'::INTERVAL PRECEDING AND CURRENT ROW),
           w_12h AS (PARTITION BY diuresi_oraria.hadm_id ORDER BY diuresi_oraria.charttime RANGE BETWEEN '12:00:00'::INTERVAL PRECEDING AND CURRENT ROW),
           w_24h AS (PARTITION BY diuresi_oraria.hadm_id ORDER BY diuresi_oraria.charttime RANGE BETWEEN '24:00:00'::INTERVAL PRECEDING AND CURRENT ROW)
),

--  Calcola lo stadio AKI secondo l'output urinario/diuresi normalized per kg/ora (Criteri KDIGO)
aki_diuresi AS (
    SELECT
        diuresi_con_copertura.subject_id,
        diuresi_con_copertura.hadm_id,
        diuresi_con_copertura.charttime,
        CASE
            -- Stage 3: < 0.3 mL/kg/h per >= 24h OPPURE anuria per >= 12h
            WHEN diuresi_con_copertura.ore_coperte_24h >= 24::DOUBLE PRECISION
             AND (diuresi_con_copertura.urine_24h / NULLIF(diuresi_con_copertura.peso_kg * 24.0::DOUBLE PRECISION, 0::DOUBLE PRECISION)) < 0.3::DOUBLE PRECISION THEN 3
            WHEN diuresi_con_copertura.ore_coperte_12h >= 12::DOUBLE PRECISION
             AND diuresi_con_copertura.urine_12h = 0::DOUBLE PRECISION THEN 3
            -- Stage 2: < 0.5 mL/kg/h per >= 12h
            WHEN diuresi_con_copertura.ore_coperte_12h >= 12::DOUBLE PRECISION
             AND (diuresi_con_copertura.urine_12h / NULLIF(diuresi_con_copertura.peso_kg * 12.0::DOUBLE PRECISION, 0::DOUBLE PRECISION)) < 0.5::DOUBLE PRECISION THEN 2
            -- Stage 1: < 0.5 mL/kg/h per >= 6h
            WHEN diuresi_con_copertura.ore_coperte_6h >= 6::DOUBLE PRECISION
             AND (diuresi_con_copertura.urine_6h / NULLIF(diuresi_con_copertura.peso_kg * 6.0::DOUBLE PRECISION, 0::DOUBLE PRECISION)) < 0.5::DOUBLE PRECISION THEN 1
            ELSE 0
        END AS stage_diuresi
    FROM diuresi_con_copertura
),

--  Unisce tutti i timestamp unici (sia di creatinina che di diuresi) per sincronizzarli
istanti AS (
    SELECT aki_creatina.hadm_id, aki_creatina.subject_id, aki_creatina.charttime FROM aki_creatina
    UNION
    SELECT aki_diuresi.hadm_id, aki_diuresi.subject_id, aki_diuresi.charttime FROM aki_diuresi
),

-- Deduplica le misurazioni di creatinina sullo stesso timestamp mantenendo lo stadio massimo
aki_creatina_dedup AS (
    SELECT aki_creatina.hadm_id, aki_creatina.charttime, MAX(aki_creatina.stage_creatina) AS stage_creatina
    FROM aki_creatina
    GROUP BY aki_creatina.hadm_id, aki_creatina.charttime
),

-- Deduplica le misurazioni di diuresi sullo stesso timestamp mantenendo lo stadio massimo
aki_diuresi_dedup AS (
    SELECT aki_diuresi.hadm_id, aki_diuresi.charttime, MAX(aki_diuresi.stage_diuresi) AS stage_diuresi
    FROM aki_diuresi
    GROUP BY aki_diuresi.hadm_id, aki_diuresi.charttime
),

--  Applica il Forward Fill per la Creatinina (mantiene l'ultimo stadio noto per i timestamp successivi)
con_stage_creat AS (
    SELECT
        sub.hadm_id,
        sub.subject_id,
        sub.charttime,
        MAX(sub.stage_creatina_raw) OVER (PARTITION BY sub.hadm_id, sub.grp) AS stage_creatina
    FROM (
        SELECT
            i.hadm_id,
            i.subject_id,
            i.charttime,
            ac.stage_creatina AS stage_creatina_raw,
            COUNT(ac.stage_creatina) OVER (PARTITION BY i.hadm_id ORDER BY i.charttime ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS grp
        FROM istanti i
        LEFT JOIN aki_creatina_dedup ac ON ac.hadm_id = i.hadm_id AND ac.charttime = i.charttime
    ) sub
),

--  Applica il Forward Fill per la Diuresi (mantiene l'ultimo stadio noto per i timestamp successivi)
con_stage_diuresi AS (
    SELECT
        sub.hadm_id,
        sub.subject_id,
        sub.charttime,
        MAX(sub.stage_diuresi_raw) OVER (PARTITION BY sub.hadm_id, sub.grp) AS stage_diuresi
    FROM (
        SELECT
            i.hadm_id,
            i.subject_id,
            i.charttime,
            ad.stage_diuresi AS stage_diuresi_raw,
            COUNT(ad.stage_diuresi) OVER (PARTITION BY i.hadm_id ORDER BY i.charttime ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS grp
        FROM istanti i
        LEFT JOIN aki_diuresi_dedup ad ON ad.hadm_id = i.hadm_id AND ad.charttime = i.charttime
    ) sub
)

--  Selezione finale: determina lo stadio AKI complessivo prendendo il peggiore (GREATEST) tra Creatinina e Diuresi
SELECT
    c.subject_id,
    c.hadm_id,
    c.charttime,
    GREATEST(COALESCE(c.stage_creatina, 0), COALESCE(d.stage_diuresi, 0)) AS aki
FROM con_stage_creat c
JOIN con_stage_diuresi d ON c.hadm_id = d.hadm_id AND c.charttime = d.charttime
ORDER BY c.subject_id, c.hadm_id, c.charttime;

-- Creazione dell'indice composito per ottimizzare le ricerche temporali su paziente e ricovero
CREATE INDEX idx_aki
    ON aki (subject_id, hadm_id, charttime);