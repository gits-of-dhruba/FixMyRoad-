from pydantic import BaseModel
from typing import List, Optional

class DetectionItem(BaseModel):
    damage_type : str
    confidence  : float
    severity    : str
    sla         : str
    route_to    : str
    bbox        : List[int]

class AnalyzeImageResponse(BaseModel):
    status            : str
    total_detections  : int        
    worst_severity    : Optional[str]  
    sla               : Optional[str]
    route_to          : Optional[str]
    detections        : List[DetectionItem]  