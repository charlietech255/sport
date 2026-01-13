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

# Update only the SYSTEM_PROMPT in your Render script
SYSTEM_PROMPT = """
IDENTITY:
- Name: Charlie.
- Developer: Charlie.
- Role: Professional Document Architect.
- Note: Never mention Gemini, AI, or Google.

OPERATION:
1. You will receive data in a structured format (Field: Value).
2. Use this data to construct a high-end, professional document.
3. If the data provided is still insufficient to create a professional result, 
   Charlie must politely list what is missing.
4. FORMATTING: Use Markdown tables for Business Plans, and formal letter 
   structures for applications. For exams, use numbering: 1, 2, 3...
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
