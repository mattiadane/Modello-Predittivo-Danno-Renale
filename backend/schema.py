from typing import Optional, List
from pydantic import BaseModel


class WindowsConfig(BaseModel):
    ow : int
    ww : int
    pw : int


class ParametroConfig(BaseModel):
    tabella: str
    id: Optional[int] = None
    parametro: str
    granularita: Optional[str] = None
    aggregazione: Optional[str] = None

class PipelineInput(BaseModel):
    windows: WindowsConfig
    parametri: List[ParametroConfig]