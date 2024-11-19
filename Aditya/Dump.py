from fastapi import APIRouter, HTTPException, File, Form, UploadFile, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from src.model.ai_model import AIModel
from cachetools import TTLCache
from datetime import datetime, timedelta
from typing import List
import pandas as pd
import csv
from io import StringIO
import markdown
import re
import os
import io

# Initialize the AIModel
ai_model = AIModel()
cache = TTLCache(maxsize=100, ttl=1200)

# Pydantic models for request and response
class SCDRequest(BaseModel):
    user_prompt: str
    service: str
    additional_controls: List[str]
    azure_controls: List[str]
    benchmark_controls: List[str]

class SCDResponse(BaseModel):
    scd: str

class FormatRequest(BaseModel):
    scd: str
    format: str
    filename: str

# Create a router object
router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application"}

# Simulated session check
async def check_session(request):
    return True

@router.post("/upload")
async def handle_file_upload(
    user_prompt: str = Form(...),
    service: str = Form(...),
    additional_controls: List[str] = Form(None),
    file: UploadFile = File(...),
    session_valid: bool = Depends(check_session),
):
    if not session_valid:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")

    # Ensure the file type is either CSV or Markdown
    if file.content_type == "text/csv":
        # Process CSV file
        contents = await file.read()
        csv_data = StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)
        data_list = [row for row in reader]  # Extract CSV rows as a list of dicts

        # Generate payload for CSV file
        generated_payload = {
            "file_type": "CSV",
            "data_summary": data_list[:2],  # Summary of first two rows
            "file_name": file.filename,
        }
    elif file.content_type == "text/markdown":
        # Process Markdown file
        contents = await file.read()
        md_content = contents.decode('utf-8')

        # Generate payload for Markdown file
        generated_payload = {
            "file_type": "Markdown",
            "content_preview": md_content[:200],  # Preview of first 200 characters
            "file_name": file.filename,
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only CSV and Markdown files are allowed.")

    # Store the generated payload in the cache
    cache[file.filename] = generated_payload

    # Combine the file payload with the SCD payload from the form
    scd_payload = {
        "user_prompt": user_prompt,
        "service": service,
        "additional_controls": additional_controls,
    }

    # Example response combining file payload and SCD payload
    response = {
        "message": f"File '{file.filename}' uploaded successfully!",
        "file_payload": generated_payload,
        "scd_payload": scd_payload,
        "cached": True,
    }

    return JSONResponse(content=response)

@router.post("/generate-scd", response_model=SCDResponse)
def generate_scd(request: SCDRequest):
    # Extract inputs from the request
    user_prompt = request.user_prompt
    service = request.service
    additional_controls = request.additional_controls
    azure_controls = request.azure_controls
    benchmark_controls = request.benchmark_controls

    if not user_prompt:
        raise HTTPException(status_code=400, detail="User prompt is required")

    # Generate the SCD using the AI model
    try:
        scd = ai_model.generate_scd(
            user_prompt=user_prompt,
            service=service,
            additional_controls=additional_controls,
            azure_controls=azure_controls,
            benchmark_controls=benchmark_controls,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SCD: {str(e)}")

    return SCDResponse(scd=scd)

@router.post("/convert-scd")
def convert_scd(request: FormatRequest):
    scd = request.scd
    format = request.format.lower()
    filename = request.filename

    if format not in ["csv", "xlsx", "md"]:
        raise HTTPException(status_code=400, detail="Invalid format specified. Choose from 'csv', 'xlsx', or 'md'.")

    # Save the SCD to the desired format
    output_file_path = f"{filename}.{format}"
    save_scd(scd, output_file_path, format)

    # Serve the file as a download
    return serve_file(output_file_path, format, filename)

def save_scd(scd, output_file_path, format='md'):
    scd_entries = re.split(r'\n\s*\n', scd.strip())

    if format == 'md':
        table_headers = ["Control ID", "Control Domain", "Control Title", "Mapping to NIST CSF v1.1 control", "Client Requirement if Any", "Policy Name", "Policy Description", "Responsibility", "Frequency", "Evidence", "Implementation Details"]
        with open(output_file_path, 'w') as f:
            f.write(f"| {' | '.join(table_headers)} |\n")
            f.write(f"| {' | '.join(['-' * len(header) for header in table_headers])} |\n")

            # Write each entry as a table row
            for entry in scd_entries:
                entry_data = parse_entry(entry)
                row = "| " + " | ".join(entry_data.get(header, '') for header in table_headers) + " |\n"
                f.write(row)

    elif format in ['csv', 'xlsx']:
        csv_data = []
        for entry in scd_entries:
            csv_data.append(parse_entry(entry))

        df = pd.DataFrame(csv_data)
        if format == 'csv':
            df.to_csv(output_file_path, index=False)
        else:
            df.to_excel(output_file_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

def parse_entry(entry):
    """Parse individual SCD entry into a dictionary"""
    entry_data = {}
    for line in entry.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            entry_data[key.strip()] = value.strip()
    return entry_data

def serve_file(file_path, format, filename):
    media_type = {
        'csv': "text/csv",
        'xlsx': "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        'md': "text/markdown",
    }.get(format)

    if not media_type:
        raise ValueError(f"Unsupported format: {format}")

    with open(file_path, 'rb') as f:
        stream = io.BytesIO(f.read())
        stream.seek(0)
        response = StreamingResponse(stream, media_type=media_type)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}.{format}"
        return response
