from typing import Optional, List
from pydantic import BaseModel

class ParametroConfig(BaseModel):
    tabella: str
    id: int
    parametro: str
    granularita: Optional[str] = None
    aggregazione: Optional[str] = None

class PipelineInput(BaseModel):
    parametri: List[ParametroConfig]