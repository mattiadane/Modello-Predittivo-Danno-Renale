"""
Modulo dei modelli di dati (Pydantic Schema).

Definisce gli schemi di validazione e serializzazione per l'input della pipeline
di analisi clinica e predizione dell'Acute Kidney Injury (AKI).
"""

from typing import Optional, List
from pydantic import BaseModel


class WindowsConfig(BaseModel):
    """
    Configurazione delle finestre temporali d'analisi expressed in ore.
    """
    ow: int  # Observation Window: durata della finestra di osservazione dei parametri clinici
    ww: int  # Waiting Window: tempo di cuscinetto tra la fine dell'osservazione e l'evento
    pw: int  # Prediction Window: intervallo in cui verificare la presenza o l'insorgenza dell'AKI


class ParametroConfig(BaseModel):
    """
    Configurazione di un singolo parametro clinico da estrarre ed elaborare.
    """
    tabella: str                   # Nome della tabella/vista sorgente di MIMIC-IV (es. 'chartevents', 'labevents')
    id: Optional[int] = None       # ID identificativo dell'item (itemid); se opzionale si usa il nome del parametro
    parametro: str                 # Nome o descrizione human-readable del parametro (es. 'heart_rate', 'creatinine')
    granularita: Optional[str] = None  # Intervallo del bucket temporale di aggregazione (es. '6h')
    aggregazione: Optional[str] = None # Tipo di aggregazione SQL da applicare (es. 'Media', 'Minimo', 'Massimo')


class PipelineInput(BaseModel):
    """
    Schema radice dell'input inviato alle API.
    Contiene le impostazioni delle finestre temporali e la lista ordinata dei parametri da analizzare.
    """
    windows: WindowsConfig           # Oggetto contenente la configurazione delle finestre (OW, WW, PW)
    parametri: List[ParametroConfig] # Elenco concatenato di parametri clinici da elaborare nelle CTE a cascata