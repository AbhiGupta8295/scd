from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from fastapi.responses import JSONResponse
from src.model.ai_model import AIModel

router = APIRouter()

class SCDRequest(BaseModel):
    user_prompt: str
    service: str
    additional_controls: List[str] = []
    azure_controls: str = ""
    benchmark_controls: str = ""

class SCDResponse(BaseModel):
    scd: str

@router.post("/generate-scd", response_model=SCDResponse)
async def generate_scd(request: SCDRequest):
    try:
        if not request.user_prompt:
            raise HTTPException(status_code=400, detail="User prompt is required")
        
        ai_model = AIModel()
        scd = ai_model.generate_scd(
            user_prompt=request.user_prompt,
            service=request.service,
            additional_controls=request.additional_controls,
            azure_controls=request.azure_controls,
            benchmark_controls=request.benchmark_controls
        )
        
        return SCDResponse(scd=scd)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FormatRequest(BaseModel):
    user_prompt: str
    service: str
    additional_controls: List[str] = []
    azure_controls: str = ""
    benchmark_controls: str = ""

@router.post("/convert-scd")
async def convert_scd(request: FormatRequest):
    try:
        if not request.user_prompt:
            raise HTTPException(status_code=400, detail="User prompt is required")
            
        ai_model = AIModel()
        scd = ai_model.generate_scd(
            user_prompt=request.user_prompt,
            service=request.service,
            additional_controls=request.additional_controls,
            azure_controls=request.azure_controls,
            benchmark_controls=request.benchmark_controls
        )
        
        return JSONResponse(content={"scd": scd})
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
