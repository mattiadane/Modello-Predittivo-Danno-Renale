-- Vista materializzata per la classificazione dei farmaci in categorie terapeutiche
CREATE MATERIALIZED VIEW drugs AS
WITH farmaci_classificati AS (
    SELECT DISTINCT 
        drug AS nome,
        CASE
            -- Diuretici
            WHEN drug ILIKE ANY (ARRAY[
                '%riamterene', '%urosemide', '%ydrochlorothiazide', '%pironolactone', 
                '%olvaptan', '%hlorothiazide', '%umetanide', '%miloride', '%etolazone', 
                '%plerenone', '%hlorthalidone', '%ndapamide', '%orsemide', '%ldactone', 
                '%thacrynic acid', '%cetazolamide'
            ]) THEN 'Diuretico'

            -- Antipertensivi
            WHEN drug ILIKE ANY (ARRAY[
                '%ebivolol', '%oexipril', '%otalol', '%isinopril', '%arvedilol', 
                '%ethyldopa', '%ropranolol', '%enazepril', '%mbrisentan', '%lonidine', 
                '%indolol', '%osentan', '%inoxidil', '%rbesartan', '%razosin', 
                '%uinapril', '%ooxazosin', '%tenolol', '%iazoxide', '%smolol', 
                '%andesartan', '%adolol', '%osartan', '%aptopril', '%alsartan', 
                '%randolapril', '%cebutolol', '%amipril', '%liskiren', '%acitentan', 
                '%uanfacine'
            ]) THEN 'Antipertensivo'

            -- Nefrotossici
            WHEN drug ILIKE ANY (ARRAY[
                '%entamicin', '%ancomycin', '%obramycin', '%mikacin', '%enicillamine', 
                '%uranofin', '%ulfamethoxazole', '%rimethoprim', '%ulfametrole', 
                '%ulfamazone', '%treptomycin', '%etilmicin', '%oledronate', '%olistin', 
                '%cyclovir', '%anciclovir', '%oscavir', '%defovir', '%enofovir', 
                '%ndinavir', '%idofovir', '%yclosporine', '%acrolimus', '%rograf', 
                '%armustine', '%utamycin', '%revacid', '%amidronate', 'zometa', 
                'viread', 'crixivan', 'vistide', 'neoral', 'gliadel', 'aredia'
            ]) THEN 'Nefrotossico'

            -- Chemioterapici
            WHEN drug ILIKE ANY (ARRAY[
                '%emetrexed', '%ribulin', '%brutinib', '%abozantinib', '%sparaginase', 
                '%verolimus', '%egaspargase', '%itomycin', '%emcitabine', '%emtuzumab', 
                '%zogamicin', '%endamustine', '%arflzomib', '%rlotinib', '%envatinib', 
                '%abrafenib', '%leomycin', '%matinib', '%ivolumab', '%uxolitinib', 
                '%xaliplatin', '%ecitabine', '%orouracil', '%emsirolimus', '%actinomycin', 
                '%asatinib', '%toposide', '%apecitabine', '%simertinib', '%rinotecan', 
                '%itoxantrone', '%darubicin', '%ertuzumab', '%rsenic', '%rioxide', 
                '%rametinib', '%evacizumab', '%enetoclax', '%nagrelide', '%incristine', 
                '%acarbazine', '%emurafenib', '%rentuximab', '%edotin', '%xazomib', 
                '%entostatin', '%ituximab', '%ethotrexate', '%unitinib', '%lemtuzumab', 
                '%etuximab', '%rizotinib', '%xitinib', '%ortezomib', '%emozolomide', 
                '%ytarabine', '%isplatin', '%anitumumab', '%ladribine', '%zacitidine', 
                '%aclitaxel', '%fosfamide', '%nasidenib', '%retinoin', '%idostaurin', 
                '%apatinib', '%ralatrexate', '%arboplatin', '%yclophosphamide', '%orlatinib', 
                '%rastuzumab', '%orafenib', '%usulfan', '%ercaptopurine', '%aunorubicin', 
                '%orfimer sodium', '%elphalan', '%embrolizumab', '%lofarabine', '%oxorubicin', 
                '%nterferon alfa-2b'
            ]) THEN 'Chemioterapico'

            -- FANS (Antinfiammatori Non Steroidei)
            WHEN drug ILIKE ANY (ARRAY[
                '%todolac', '%etorolac', '%ulindac', '%elecoxib', '%iroxicam', 
                '%abumetone', '%aproxen', '%eloxicam', '%buprofen', '%lurbiprofen', 
                '%xaprozin', '%alsalate', '%iclofenac', '%ceclofenac', '%enoxicam', 
                '%ornoxicam', '%etoprofen', '%elecoxib', '%toricoxib', '%cetylsalicylic acid', 
                '%exketoprofen', '%ofecoxib', '%iaprofenic acid', '%exibuprofen', 
                '%iflumic acid', '%imesulide'
            ]) THEN 'Fans'

            -- Inotropi / Vasopressori
            WHEN drug ILIKE ANY (ARRAY[
                '%drenaline', '%oradrenaline', '%opamine', '%soprenaline', 
                '%obutamine', '%opexamine', '%phedrine', '%henylephrine'
            ]) THEN 'Dopamina'

            ELSE NULL
        END AS tipo
    FROM prescriptions
)
SELECT 
    nome, 
    tipo
FROM farmaci_classificati
WHERE tipo IS NOT NULL;

-- Indice composito per velocizzare le ricerche per nome e tipo farmaco
CREATE INDEX idx_drugs ON drugs (nome, tipo);