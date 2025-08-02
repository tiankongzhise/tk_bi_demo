from pydantic import BaseModel,Field

class AdsQueryParams(BaseModel):
    start_time: str
    end_time: str
    report_type: str|int
    time_unit: str|int

class BdAdsQueryParams(BaseModel):
    columns:list[str]
    sorts:list[dict] = Field(default_factory=list)
    filters:list[dict] = Field(default_factory=list)
    startRow:int = 1
    rowCount:int = 1000
    needSum:bool = False
    
