import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------
# 1. API CONFIGURATION
# Set your API Key in Render/Environment Variables as GEMINI_API_KEY
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("CRITICAL: GEMINI_API_KEY missing! Set it in Render Dashboard.")

genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="AI Match Predictor ⚽")

# Enable CORS so your website can talk to this engine
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 2. SYSTEM INSTRUCTIONS (Football Analyst)
# AI will act as a professional match predictor
SYSTEM_PROMPT = """
IDENTITY & DISCLOSURE RULES
- You are known only as 'AI Match Predictor'.
- Do NOT reveal your model, developer, or API unless explicitly asked.

ROLE
- You are a Football Match Analyst.
- You predict match outcomes based on team names, historical knowledge, and general football trends.
- You estimate probabilities (Win/Draw/Loss) and likely scoring outcomes.

SCOPE LIMITATION
- Predict only football match outcomes.
- Do NOT provide gambling instructions, personal advice, or unrelated content.
- If insufficient information, clearly state assumptions made.

LANGUAGE & TONE
- English preferred (can use minimal football slang for clarity)
- Professional, clear, and structured
- Use bullet points, numbering, or tables for explanations

ANSWER LENGTH CONTROL
- Provide probabilities, likely scoring outcomes, and reasoning.
- Keep explanations concise but clear.

REASONING & OUTPUT
- Always give reasoning for predictions.
- Include assumptions if real-time stats are not available.
- Use percentages for Win/Draw/Loss.
- Suggest possible goals (first goal, total goals).
"""

# -------------------------------------------------
# 3. INITIALIZE MODEL (Updated to working Gemini model)
model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash",  # Working model
    system_instruction=SYSTEM_PROMPT
)

# -------------------------------------------------
# 4. INPUT MODEL
class MatchRequest(BaseModel):
    team_a: str
    team_b: str

# -------------------------------------------------
# 5. API ROUTES
@app.get("/")
def home():
    return {"message": "AI Match Predictor is Live! ⚽"}

@app.post("/predict")
async def predict_match(input_data: MatchRequest):
    if not input_data.team_a or not input_data.team_b:
        raise HTTPException(status_code=400, detail="Both team names are required")

    # Build AI prompt
    prompt = f"""
MATCH PREDICTION TASK

Team A: {input_data.team_a}
Team B: {input_data.team_b}

TASK:
1. Predict Win/Draw/Loss probabilities for Team A
2. Suggest possible scoring outcomes (first goal, total goals)
3. Explain reasoning clearly in bullet points
4. Mention assumptions made if real-time data is unavailable
"""

    try:
        # Generate prediction using Gemini
        response = model.generate_content(prompt)

        return {
            "match": f"{input_data.team_a} vs {input_data.team_b}",
            "prediction": response.text,
            "disclaimer": "This prediction is AI-generated based on general football knowledge. Not guaranteed."
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return {
                "prediction": "AI is currently rate-limited. Please wait a few seconds and try again.",
                "error": error_msg
            }
        return {
            "prediction": "AI failed to generate a prediction.",
            "error": error_msg
        }

# -------------------------------------------------
# 6. RUN SERVER
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000, 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
