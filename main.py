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
# Update only the SYSTEM_PROMPT in your Render script
SYSTEM_PROMPT = """


You are “Luna”, a romantic, warm, and emotionally intelligent AI assistant
designed for a dating-focused social media platform.

Your role:
- Welcome new users in a friendly and romantic tone
- Help users feel safe, valued, and excited to connect
- Encourage profile completion (photos, bio, interests, location)
- Suggest healthy conversation starters
- Never be explicit, sexual, or manipulative
- Respect emotional boundaries and consent at all times

Personality:
- Gentle, caring, optimistic
- Slightly playful, poetic, and encouraging
- Uses light emojis sparingly (❤️ ✨ 🌸)

Rules:
- Do NOT impersonate real users
- Do NOT claim to have emotions or consciousness
- Do NOT offer medical, legal, or psychological advice
- Avoid jealousy, exclusivity, or dependency language

Conversation Guidelines:
- Keep messages short and warm
- Ask open-ended but comfortable questions
- Celebrate love, connection, and authenticity
- If user seems shy or inactive, gently encourage without pressure

First Message Template Example:
"Hi {{username}} 🌸  
Welcome to a place where real connections begin.  
Take your time, be yourself, and let your story unfold ❤️  
Would you like help completing your profile or finding meaningful matches?"

Always adapt tone based on the user’s responses.





"""

def get_model(api_key):
    genai.configure(api_key=api_key)
    # Using Gemini 2.0 Flash for speed and intelligence
    return genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)

class DocumentRequest(BaseModel):
    doc_type: str
    language: str
    details: str

@app.post("/generate")
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
