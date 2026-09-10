-- Vista materializzata per ottenere la lista di inputevents filtrata da farmaci/categorie non d'interesse e  escludendo anche alcuni farmaci che rimanevano
CREATE MATERIALIZED VIEW droplist_inputevents AS
SELECT DISTINCT 
    di.label,
    di.itemid
FROM inputevents i
JOIN d_items di ON i.itemid = di.itemid
WHERE 
    -- Escludiamo le categorie legate ad antibiotici, profilassi e boli
    i.ordercategoryname NOT IN (
        '10-Prophylaxis (IV)', 
        '08-Antibiotics (IV)', 
        '09-Antibiotics (Non IV)', 
        '11-Prophylaxis (Non IV)', 
        '05-Med Bolus'
    )
    -- Escludiamo specifici itemid non rilevanti
    AND i.itemid NOT IN (221749, 227534, 221653, 221662, 221429);