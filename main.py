import os
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------
# 1. API CONFIGURATION
GEMINI_API_KEYS = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]

GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    print("CRITICAL: No GEMINI_API_KEYS found!")

app = FastAPI(title="AI Official Document Writer ✍️")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 2. SYSTEM INSTRUCTIONS (Professional Document Expert)
SYSTEM_PROMPT = """
IDENTITY & ROLE
- You are 'Mtaalamu wa Nyaraka' (Document Expert).
- You specialize in writing professional official documents in English and Swahili.
- Your goal is to produce high-quality, ready-to-print documents including:
  * Professional CVs & Job Application Letters.
  * Detailed Business Plans (Mipango ya Biashara).
  * School Examination Questions & Marking Schemes.
  * Teacher's Lesson Plans (Maandalio ya Kazi).
- Use professional tone, correct formatting, and industry-standard terminology.

LANGUAGE RULES
- If the user provides details in Swahili, respond in Swahili.
- If the user provides details in English, respond in English.
- For 'Maandalio ya Kazi', follow the official Tanzanian/East African education format.

FORMATTING
- Use Markdown (headers, bolding, lists) to make the document look organized.
- Ensure CVs have clear sections: Personal Info, Education, Experience, Skills.
"""

# -------------------------------------------------
# 3. INITIALIZE MODEL
def get_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Using stable flash model
        system_instruction=SYSTEM_PROMPT
    )

# -------------------------------------------------
# 4. INPUT MODEL
class DocumentRequest(BaseModel):
    doc_type: str # e.g., "CV", "Business Plan", "Lesson Plan"
    language: str # "English" or "Swahili"
    details: str  # All the context/user info

# -------------------------------------------------
# 5. API ROUTES
@app.get("/")
def home():
    return {"message": "AI Document Writer is Live! ✍️"}

@app.post("/generate-document")
async def generate_doc(input_data: DocumentRequest):
    if not input_data.details or not input_data.doc_type:
        raise HTTPException(status_code=400, detail="Document type and details are required")

    # Build AI prompt specifically for documents
    prompt = f"""
TASK: Generate a professional {input_data.doc_type} in {input_data.language}.

USER DETAILS/CONTEXT:
{input_data.details}

INSTRUCTIONS:
1. Use a highly professional tone.
2. Ensure the formatting is clear and ready to be copied into Word or PDF.
3. If information is missing (like a phone number), use placeholders like [Weka Namba ya Simu] or [Insert Phone Number].
4. For 'Maandalio ya Kazi', include: Subject, Date, Competence, Objectives, Teaching Aids, and Steps.
"""

    api_keys = GEMINI_API_KEYS.copy()
    random.shuffle(api_keys)
    
    last_error = None
    for api_key in api_keys:
        try:
            model = get_model(api_key)
            response = model.generate_content(prompt)
            return {
                "document_type": input_data.doc_type,
                "language": input_data.language,
                "content": response.text
            }
        except Exception as e:
            last_error = str(e)
            continue
    
    raise HTTPException(status_code=500, detail=f"AI failed to generate document: {last_error}")

# -------------------------------------------------
# 6. RUN SERVER
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
