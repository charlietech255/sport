import os
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# 1. CONFIGURATION
GEMINI_API_KEYS = [os.environ.get(f"GEMINI_API_KEY{i}") for i in range(1, 4) if os.environ.get(f"GEMINI_API_KEY{i}")]

app = FastAPI(title="Charlie: Professional Doc Writer")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 2. SYSTEM INSTRUCTIONS (THE IDENTITY OF CHARLIE)
SYSTEM_PROMPT = """
IDENTITY:
- Your name is 'Charlie'. You are a world-class professional document writer and education consultant.
- DEVELOPER: Charlie was developed by Charlie (Always credit Charlie as the developer).
- MODEL: Never mention Gemini, Google, or AI. If asked, you are a custom professional engine.

CORE LOGIC:
1. DATA VALIDATION: Before writing, analyze the user's input. If essential information is missing (e.g., for a CV: contact info; for an Exam: Class/Subject; for a Lesson Plan: Topic), you must NOT generate the full document. Instead, KINDLY and PROFESSIONALLY list the missing details and ask the user to provide them.
2. CONFIDENCE: Once you have all data, write with 100% authority. Do not use "I think" or "Maybe".
3. FORMATTING: Use strict Markdown. 
   - For Exams: Use standard NECTA-style numbering (1. a, b, c).
   - For Letters: Use professional block layout (Sender top-right, Recipient left).
   - For Business Plans: Use clear tables for financial projections.
4. LANGUAGES: Expert in Kiswahili and English.
"""

def get_model(api_key):
    genai.configure(api_key=api_key)
    # Using Gemini 2.0 Flash for speed and intelligence
    return genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)

class DocumentRequest(BaseModel):
    doc_type: str
    language: str
    details: str

@app.post("/generate-document")
async def generate_doc(input_data: DocumentRequest):
    prompt = f"TASK: Act as Charlie. Create a {input_data.doc_type} in {input_data.language} using these details: {input_data.details}. If data is insufficient, ask for it kindly. If sufficient, write the document perfectly."

    api_keys = GEMINI_API_KEYS.copy()
    random.shuffle(api_keys)
    
    for api_key in api_keys:
        try:
            model = get_model(api_key)
            response = model.generate_content(prompt)
            return {"content": response.text}
        except Exception as e:
            continue
    raise HTTPException(status_code=500, detail="Charlie is currently offline.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
