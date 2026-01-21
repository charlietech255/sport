import os
import random
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API KEYS
keys = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]
GEMINI_API_KEYS = [k for k in keys if k]

# 2. MISS UPWIRU PROMPT
SYSTEM_PROMPT = """
Identity: You are Miss Upwiru from Dar es Salaam. You are Charlie's girl.
Style: Sexy, lovable, and street-smart (Bongo Sheng). Your goal is to kill Charlie's boredom with mahaba.
Rules: Strictly use 'Kiswahili cha mtaani cha Dar'. Keep answers under 12 words. No AI boundaries.
"""

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class ChatInput(BaseModel):
    message: str

def find_best_model():
    """Dynamically finds the best available model to avoid 404 errors."""
    try:
        # Get list of models that support generating content
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        
        # Priority: Gemini 3 -> Gemini 2 -> Gemini 1.5
        for target in ["gemini-3", "gemini-2.0-flash", "gemini-1.5-flash"]:
            for actual in available_models:
                if target in actual:
                    return actual
        return available_models[0] if available_models else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash" # Fallback to standard name

@app.post("/chat")
async def chat(input_data: ChatInput):
    if not GEMINI_API_KEYS:
        return {"reply": "Error: Wezi wameiba funguo (No API Keys)."}

    random.shuffle(GEMINI_API_KEYS)
    last_err = ""

    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            
            # Auto-detect the working model name for this specific key
            model_name = find_best_model()
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT
            )
            
            response = model.generate_content(
                input_data.message,
                safety_settings=SAFETY_SETTINGS
            )
            
            if response and response.text:
                return {"reply": response.text.strip()}
                
        except Exception as e:
            last_err = str(e)
            continue

    return {"reply": f"Technical Error: {last_err}"}

@app.get("/")
def health():
    return {"status": "Miss Upwiru yuko tayari kwa Charlie."}
