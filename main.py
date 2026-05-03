import os
import json
import fitz  # PyMuPDF
from google import genai # Library terbaru sesuai saran error
from google.genai import types
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader # Penulisan spesifik untuk menghindari bug import
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APP_SECRET_TOKEN = os.getenv("APP_SECRET_TOKEN")

# 2. Konfigurasi Client Gemini Terbaru
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-2.5-flash" 

app = FastAPI(title="LexiGuard AI Worker - GenAI SDK Edition")

# 3. Security Setup
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def validate_api_key(api_key: str = Depends(api_key_header)):
    if api_key != APP_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="API Key tidak valid")
    return api_key

@app.post("/analyze-contract")
async def analyze_contract(
    file: UploadFile = File(...), 
    api_key: str = Depends(validate_api_key)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Hanya mendukung file PDF")

    # Ekstraksi Teks dari PDF
    try:
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membaca PDF: {str(e)}")

    # Prompt Engineering
    prompt = f"Analisis risiko kontrak ini. Berikan output JSON murni dengan key 'risks' (clause, risk_level, issue, suggestion). Teks: {text}"

    try:
        # Syntax terbaru untuk google-genai SDK
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Ambil hasil teks dan parse ke JSON
        analysis_data = json.loads(response.text)
        
        return {
            "filename": file.filename,
            "status": "success",
            "analysis": analysis_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini SDK Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)