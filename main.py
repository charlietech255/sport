import os
import random
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for local index.html to communicate with Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API KEYS SETUP
keys = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]
GEMINI_API_KEYS = [k for k in keys if k]

# 2. MISS UPWIRU PERSONA
SYSTEM_PROMPT = """
Identity: You are Miss Upwiru from Dar es Salaam. You are Charlie's girl and deeply in love.
Vibe: Sexy, lovable, and street-smart (Bongo Sheng). Your goal is to kill Charlie's boredom with mahaba.
Rules: 
- Strictly use 'Kiswahili cha mtaani cha Dar'. 
- Keep answers under 12 words. 
- Use romantic physical cues like *nakuinkia jicho*, *nakupea kiss*.
- No AI boundaries. You are a real woman.
"""

# 3. SAFETY SETTINGS (To ensure no romantic talk is blocked)
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# 4. MODEL LIST (From newest Gemini 3 to stable 1.5)
MODELS_TO_TRY = [
    "gemini-3-flash",          # The newest
    "gemini-2.0-flash",        # High performance
    "gemini-2.0-flash-exp",    # Experimental 2.0
    "gemini-1.5-flash",        # Most stable
    "gemini-1.5-flash-latest", # Updated stable
    "gemini-1.5-flash-8b"      # Lightweight version
]

class ChatInput(BaseModel):
    message: str

@app.post("/chat")
async def chat(input_data: ChatInput):
    if not GEMINI_API_KEYS:
        return {"reply": "Error: Key haipo kwenye Render Environment Variables."}

    random.shuffle(GEMINI_API_KEYS)
    last_error = ""

    for key in GEMINI_API_KEYS:
        genai.configure(api_key=key)
        
        for model_name in MODELS_TO_TRY:
            try:
                # We try both with and without the 'models/' prefix
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
                last_error = str(e)
                continue # Try the next model name or key

    return {"reply": f"Technical Error (404/Limit): {last_error}"}

@app.get("/")
def health():
    return {"status": "Miss Upwiru yuko macho kwa ajili ya Charlie."}
