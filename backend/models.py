from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class NLQueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)

class SQLAnalyzeRequest(BaseModel):
    sql: str = Field(..., min_length=6, max_length=5000)

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None