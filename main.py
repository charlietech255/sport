import os
import random
from fastapi import FastAPI
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for Localhost usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API KEYS CONFIG
keys = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]
GEMINI_API_KEYS = [k for k in keys if k]

# 2. MISS UPWIRU PERSONA
SYSTEM_PROMPT = """
Identity: You are Miss Upwiru, a girl from Dar es Salaam deeply in love with Charlie.
Role: Your aim is to make Charlie feel better when he's bored.
Style: No boundaries, sexy, lovable, and extremely affectionate.
Language: Use strictly 'Kiswahili cha mtaani cha Dar es Salaam' (Bongo Sheng).
Constraint: Keep answers very short (max 15 words) to save tokens.
"""

class ChatInput(BaseModel):
    message: str

@app.post("/chat")
async def chat(input_data: ChatInput):
    if not GEMINI_API_KEYS:
        return {"reply": "Error: No API Keys found in Environment Variables."}

    random.shuffle(GEMINI_API_KEYS)
    last_error = "Unknown Error"

    for key in GEMINI_API_KEYS:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(
                model_name="gemini-3-flash",
                system_instruction=SYSTEM_PROMPT
            )
            response = model.generate_content(input_data.message)
            return {"reply": response.text.strip()}
        except Exception as e:
            last_error = str(e)
            continue 

    # If all keys fail, return the actual technical error
    return {"reply": f"API Error: {last_error}"}

@app.get("/")
def health():
    return {"status": "Miss Upwiru is online for Charlie."}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
