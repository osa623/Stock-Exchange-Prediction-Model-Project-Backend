from pydantic import BaseModel

class StockResponseFree(BaseModel):
    symbol: str
    company_name: str
    price: float
    note: str

class StockResponsePremium(BaseModel):
    symbol: str
    company_name: str
    price: float
    valuation_summary: dict
    ratios: dict
    cashflow_summary: dict
