-- view create per non diventare matto durante la generazione delle query in python

CREATE VIEW v_chartevents(subject_id, hadm_id, stay_id, itemid, valid_time, val) AS
SELECT chartevents.subject_id,
       chartevents.hadm_id,
       chartevents.stay_id,
       chartevents.itemid,
       chartevents.charttime AS valid_time,
       chartevents.valuenum  AS val
FROM chartevents;



CREATE VIEW v_inputevents(subject_id, hadm_id, stay_id, itemid, input_name, valid_time) AS
SELECT i.subject_id,
       i.hadm_id,
       i.stay_id,
       i.itemid,
       d.label     AS input_name,
       i.starttime AS valid_time
FROM inputevents i
         JOIN d_items d ON i.itemid = d.itemid;

CREATE VIEW v_labevents(subject_id, hadm_id, itemid, valid_time, val) AS
SELECT labevents.subject_id,
       labevents.hadm_id,
       labevents.itemid,
       labevents.charttime AS valid_time,
       labevents.valuenum  AS val
FROM labevents;



CREATE VIEW  v_procedureevents(subject_id, hadm_id, stay_id, itemid, procedure_name, valid_time) AS
SELECT p.subject_id,
       p.hadm_id,
       p.stay_id,
       p.itemid,
       d.label     AS procedure_name,
       p.starttime AS valid_time
FROM procedureevents p
         JOIN d_items d ON p.itemid = d.itemid;

CREATE VIEW v_outputevents(subject_id, hadm_id, stay_id, itemid, valid_time, val) AS
SELECT outputevents.subject_id,
       outputevents.hadm_id,
       outputevents.stay_id,
       outputevents.itemid,
       outputevents.charttime AS valid_time,
       outputevents.value     AS val
FROM outputevents;

CREATE VIEW v_prescriptions(subject_id, hadm_id, drug, tipo, starttime, stoptime) AS
SELECT p.subject_id,
       p.hadm_id,
       p.drug,
       d.tipo,
       p.starttime,
       p.stoptime
FROM prescriptions p
         JOIN drugs d ON p.drug::text = d.nome::text;



