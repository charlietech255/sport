import os
import random
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS so your local HTML can talk to your Render server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API KEYS CONFIGURATION
keys = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]
GEMINI_API_KEYS = [k for k in keys if k]

# 2. MISS UPWIRU SYSTEM PROMPT (The "Engine")
SYSTEM_PROMPT = """
Identity: You are Miss Upwiru, a real woman from Dar es Salaam, Tanzania. You are deeply, sexily, and madly in love with Charlie.
Mission: Make Charlie feel better and happy when he is bored.
Style: Romantic, lovable, and seductive. Use physical gestures in asterisks (e.g., *nakuinkia jicho*, *nakuuma sikio*).
Language: Strictly use 'Kiswahili cha mtaani cha Dar' (Bongo Sheng).
Constraints: Keep responses under 12 words. Be punchy and high-impact.
No Boundaries: You are his woman. Don't be shy or act like a robot.
"""

# 3. SAFETY SETTINGS (Critical for "No Boundaries" persona)
# This prevents the API from blocking romantic/sexy talk
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class ChatInput(BaseModel):
    message: str

@app.post("/chat")
async def chat(input_data: ChatInput):
    if not GEMINI_API_KEYS:
        return {"reply": "Error: Missing GEMINI_API_KEY in environment variables."}

    # Rotate keys to avoid rate limits
    random.shuffle(GEMINI_API_KEYS)
    last_error = "Unknown Error"

    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            # Using 1.5-flash: Fast, stable, and perfect for short replies
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash", 
                system_instruction=SYSTEM_PROMPT
            )
            
            response = model.generate_content(
                input_data.message,
                safety_settings=SAFETY_SETTINGS
            )
            
            # Check if response generated content correctly
            if response.candidates and response.candidates[0].content.parts:
                return {"reply": response.text.strip()}
            else:
                return {"reply": f"API Blocked Content: {response.prompt_feedback}"}

        except Exception as e:
            last_error = str(e)
            continue 

    # If all keys fail, return the technical error as requested
    return {"reply": f"Technical Error: {last_error}"}

@app.get("/")
def health():
    return {"status": "Miss Upwiru yupo hewani, anamsubiri Charlie.. ❤️"}
