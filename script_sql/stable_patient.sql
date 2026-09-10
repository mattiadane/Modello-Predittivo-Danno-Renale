-- Creazione della vista materializzata per identificare i pazienti "stabili" basandosi sulla creatinina (dataset MIMIC-IV)
CREATE MATERIALIZED VIEW stable_patient AS

--  Identifica il primo ricovero in Terapia Intensiva (ICU) per ciascun paziente
WITH first_icu_stays AS (
    SELECT
        icustays.subject_id,
        icustays.hadm_id,
        icustays.intime,
        icustays.stay_id,
        icustays.outtime,
        -- Ordina i ricoveri ICU del paziente per data d'ingresso per trovare il primo
        ROW_NUMBER() OVER (PARTITION BY icustays.subject_id ORDER BY icustays.intime) AS icu_order
    FROM icustays
),

--  Estrae e ordina cronologicamente le misurazioni di creatinina per i pazienti eleggibili
creatinine_stability AS (
    SELECT
        f.subject_id,
        f.stay_id,
        f.hadm_id,
        l.valuenum,
        -- Numera le misurazioni di creatinina in ordine di tempo a partire dall'ingresso in ICU
        ROW_NUMBER() OVER (PARTITION BY f.stay_id ORDER BY l.charttime) AS rn
    FROM first_icu_stays f
    JOIN mimic_iv_2_2_untouched.labevents l ON f.hadm_id = l.hadm_id
    JOIN mimic_iv_2_2_untouched.patients p ON f.subject_id = p.subject_id
    WHERE f.icu_order = 1                               -- Considera solo il primo ricovero in ICU
      AND l.itemid = 50912                             -- Codice per la Creatinina nei labevents di MIMIC
      AND l.charttime >= f.intime                      -- Solo misurazioni effettuate dopo l'ingresso in ICU
      AND p.anchor_age >= 18 AND p.anchor_age <= 90   -- Criterio di inclusione: età compresa tra 18 e 90 anni
      AND l.valuenum IS NOT NULL                        -- Esclude valori mancanti/nulli
),

--  Confronta le prime due misurazioni di creatinina per verificare la stabilità renale
stable_cohort AS (
    SELECT
        c1.subject_id,
        c1.hadm_id,
        c1.stay_id
    FROM creatinine_stability c1
    -- Self-join per affiancare la prima (c1) e la seconda (c2) misurazione dello stesso ricovero
    JOIN creatinine_stability c2 ON c1.hadm_id = c2.hadm_id
    WHERE c1.rn = 1
      AND c2.rn = 2
      -- Definisce "stabile" il paziente con una variazione assoluta di creatinina inferiore a 0.3 mg/dL
      AND ABS(c2.valuenum - c1.valuenum) < 0.3::DOUBLE PRECISION
)

-- Selezione finale della coorte di pazienti stabili
SELECT
    stable_cohort.subject_id,
    stable_cohort.hadm_id,
    stable_cohort.stay_id
FROM stable_cohort;

-- Creazione dell'indice su stay_id per velocizzare le future query di join sulla vista materializzata
CREATE INDEX stable_patient_idx
    ON stable_patient (stay_id);