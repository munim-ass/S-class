from fastapi import FastAPI, UploadFile, File, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fpdf import FPDF
import numpy as np
import cv2
import json
import io
from groq import Groq
import easyocr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use your actual API Key
client = Groq(api_key="GROQ_API_KEY") 
reader = easyocr.Reader(['en'])

class StudySession:
    all_text = ""

session = StudySession()

@app.post("/sync-board")
async def sync_board(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    results = reader.readtext(img, detail=0)
    detected_text = " ".join(results)
    
    if detected_text.strip():
        session.all_text += " " + detected_text
        return {"raw_text": detected_text}
    return {"raw_text": ""}

@app.post("/generate-final-notes")
async def generate_notes(payload: dict = None):
    text_to_analyze = payload.get("all_text", session.all_text) if payload else session.all_text
    if not text_to_analyze.strip():
        text_to_analyze = "General educational concepts"

    prompt = f"""
    Create a professional study guide from this text: "{text_to_analyze}"
    You MUST return ONLY a JSON object. No conversational text.
    
    Format:
    {{
      "notes": [
        {{
          "title": "Topic Name",
          "definition": "3-sentence professional explanation.",
          "image_url": "Diagram description"
        }}
      ],
      "cheatsheet": {{
        "Quick Facts": ["Point 1", "Point 2"]
      }},
      "quiz": [
        {{ "question": "Question text?", "answer": "Detailed answer" }}
      ]
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a JSON-only API. No markdown code blocks."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile", # Updated model name
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)

    except Exception as e:
        print(f"AI Error: {e}")
        return {"notes": [], "cheatsheet": {}, "quiz": []}

@app.post("/generate-pdf")
async def get_pdf(payload: dict):
    try:
        data = payload.get("studyData", {})
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 20, "S-CLASS STUDY GUIDE", ln=True, align="C")
        
        # Notes
        pdf.set_font("helvetica", "B", 18)
        pdf.cell(0, 10, "1. Notes", ln=True)
        for note in data.get("notes", []):
            pdf.set_font("helvetica", "B", 14)
            pdf.multi_cell(0, 10, text=str(note.get("title", "Topic")))
            pdf.set_font("helvetica", "", 12)
            pdf.multi_cell(0, 8, text=str(note.get("definition", "")))
            pdf.ln(5)

        pdf_bytes = pdf.output()
        return Response(
            content=bytes(pdf_bytes), # Fix for bytearray encode error
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=StudyGuide.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
