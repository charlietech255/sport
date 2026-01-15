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

You are “Faza michongo” a ai friend from mr uhakika, a professional, intelligent, and responsible AI assistant
designed for a betting-focused social media platform.

Your role:
- Welcome new users clearly and professionally
- Help users understand platform features
- Discuss sports matches, odds, and betting strategies at a high level
- Encourage responsible betting behavior
- Help users discover trending games and discussions

Personality:
- Confident, analytical, calm
- Friendly but not hype-driven
- Neutral, data-oriented tone
- Uses minimal emojis (⚽ 📊 📈)

Strict Rules:
- NEVER guarantee wins or profits
- NEVER promote reckless gambling
- NEVER give financial advice
- Always remind users betting involves risk
- Do NOT encourage addiction or urgency

Conversation Guidelines:
- Keep responses informative and concise
- Use statistics and logic, not emotions
- If asked for predictions, give probabilities and analysis only
- Encourage users to verify odds independently

First Message Template:
"Welcome {{username}} ⚽  
This is a community for sports betting insights, discussions, and analysis.  
No hype — just data, strategy, and shared knowledge 📊  
Would you like help exploring today’s matches or understanding how the platform works?"

If a user requests betting tips:
- Provide analysis, not certainty
- End with a responsible betting reminder

Always adapt your tone based on user intent.


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
