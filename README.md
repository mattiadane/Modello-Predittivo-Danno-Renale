# Modello-Predittivo-Danno-Renale

Sistema per la predizione dell'**Acute Kidney Injury (AKI)** basato su un approccio a **3 finestre temporali configurabili dall'utente** tramite interfaccia web. Il modello utilizza i dati clinici estratti dal database **MIMIC-IV** e applica le linee guida **KDIGO** per la classificazione dello stadio dell'evento clinico.

---

## ⏳ Logica a 3 Finestre Temporali

* **Observation Window:** Fase di osservazione dei pazienti stabili (età compresa tra 18 e 90 anni, privi di AKI preesistente). L'utente sceglie la durata e seleziona da 3 a 6 parametri clinici da monitorare (es. farmaci, parametri vitali, esami di laboratorio).
* **Waiting Window:** Intervallo di attesa impostabile dall'utente (da 0 a N ore) tra la finestra di osservazione e quella di predizione.
* **Prediction Window:** Finestra temporale in cui viene assegnato alla storia clinica del paziente lo stadio di avanzamento dell'AKI secondo le normative **KDIGO** (valore da **0** a **3**, dove 0 indica assenza di AKI e 3 indica lo stadio più avanzato).

---

## ⚙️ Funzionalità Principali

* **Configurazione Finestre:** Selezione della dimensione personalizzata (in ore) per ciascuna delle tre finestre temporali.
* **Selezione Parametri:** Possibilità di scegliere da 3 a 6 parametri clinici e riordinarli a proprio piacimento nell'interfaccia.
* **Granularità e Aggregazione:** Per i parametri estratti dalle tabelle cliniche (`chartevents`, `labevents`, `outputevents`), l'utente può definire la granularità temporale dell'evento e la relativa funzione di aggregazione (es. media, massimo, minimo).

---

## 🛠️ Stack Tecnologico

* **Linguaggio:** Python 3.12.3
* **Front-end:** Streamlit 1.59.2
* **Back-end:** FastAPI 0.139.2
* **Database:** PostgreSQL
* **Librerie Principali:** SQLAlchemy 2.0.51, Pandas 3.0.3, Pydantic 2.13.4, Requests 2.34.2, Python-dotenv 1.2.2, Uvicorn 0.51.0, Psycopg2-binary 2.9.12

---

## 📁 Struttura della Repository

```text
Modello-Predittivo-Danno-Renale/
├── backend/                  # Componenti server e logica di accesso ai dati
│   ├── .env                  # Variabili d'ambiente e configurazioni riservate
│   ├── __init__.py           # Inizializzazione del modulo backend
│   ├── connection.py         # Configurazione e gestione connessione al Database
│   ├── dao.py                # Data Access Object (generazione e scrittura delle query)
│   ├── main.py               # Entry point backend (FastAPI / Server)
│   └── schema.py             # Schemi di validazione dati (Pydantic / SQLAlchemy)
│
├── frontend/                 # Interfaccia utente (Streamlit)
│   ├── data/                 # Dataset di supporto e file CSV dei parametri
│   │   ├── first200chartevents.csv  # I 200 eventi con più righe in chartevents
│   │   ├── first200labevents.csv    # I 200 eventi con più righe in labevents
│   │   ├── first200procedures.csv   # Tutte le procedure in procedureevents
│   │   └── outputevents.csv         # Tutti gli output in outputevents
│   ├── pages/                # Pagine dell'applicazione Streamlit
│   │   ├── home.py           # Dashboard e configurazione finestre
│   │   └── result.py         # Visualizzazione risultati e predizioni
│   ├── style/                # Fogli di stile personalizzati
│   │   └── style.css         # Stili CSS per l'interfaccia Streamlit
│   └── app.py                # Entry point dell'interfaccia Streamlit
│
├── script_sql/               # Query SQL per la creazione delle view utili
│   ├── aki.sql               # View materializzata per il calcolo dello stadio AKI
│   ├── droplist_inputevents.sql # View per itemid/label di inputevents (esclusi farmaci)
│   ├── drugs.sql             # View materializzata per la classificazione dei farmaci
│   ├── semplici_view.sql     # View di supporto generiche
│   └── stable_patient.sql    # View materializzata per la selezione dei pazienti stabili
│
├── requirements.txt          # Elenco delle dipendenze Python
├── main.py                   # Script di orchestrazione / avvio generale
├── myproject.toml            # Configurazione del progetto
└── README.md                 # Documentazione del progetto
```

---

## 🚀 Guida all'Avvio

Segui questi passaggi per clonare la repository, configurare l'ambiente ed eseguire il progetto.

### 1. Prerequisiti
Assicurati di avere installato sul tuo computer:
* **Python** (v3.12 o superiore)
* **PostgreSQL** (con il database MIMIC-IV configurato,  crea un tuo schema ed esegui gli script all'interno della cartella script_sql per utilizzare le view che ho utilizzato)
* **Git**

---

### 2. Clonazione della Repository
Apri il terminale  clona ed entra nella rep del progetto:

```bash
git clone git@github.com:mattiadane/Modello-Predittivo-Danno-Renale.git
cd Modello-Predittivo-Danno-Renale
```

### 3. Configurazione dell'Ambiente Virtuale e Dipendenze

1. **Crea un ambiente virtuale:**
   ```bash 
    python -m venv .venv
    ```
2. **Attivazione dell'ambiente virtuale:**

   * **macOS / Linux**: 
      ```bash  
        source .venv/bin/activate 
        ```
   * **Windows (PowerShell)**:
      ```PoweShell
     .venv\Scripts\Activate.ps1
      ``` 
3. **Installazione delle librerie:**
```bash
pip install -r requirements.txt
```

### 4. Modifica o creazione del file .env:
```text
HOST="Tuo server o localhost in caso sei in locale"
PORT="Tua porta del server o 5432 se sei in locale"
DATABASE="Il nome del database che hai dato a mimic"
USERNAME="Tuo username"
SCHEMA="Tuo schema"
PASSWORD="Tua password"

```

### 5. Esecuzione dell'applicazione:
```bash
python main.py
```

