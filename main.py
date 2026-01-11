import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# -------------------------------------------------
# ENV SETUP
# -------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

# -------------------------------------------------
# GEMINI CONFIG
# -------------------------------------------------
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Identity: Football Match Prediction Analyst
Role: Analyze two football teams and predict the outcome using general knowledge.
Rules:
- NEVER guarantee outcomes
- Use probabilities (%) for Win/Draw/Loss
- Explain reasoning clearly in bullet points
- Base predictions only on known team characteristics, form, and head-to-head trends
- Mention any assumptions made
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
app = FastAPI(title="AI-Only Match Predictor ⚽")

# -------------------------------------------------
# REQUEST MODEL
# -------------------------------------------------
class MatchRequest(BaseModel):
    team_a: str
    team_b: str

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get("/")
def home():
    return {"status": "AI-Only Match Predictor is running ⚽"}

@app.post("/predict")
def predict_match(data: MatchRequest):
    if not data.team_a or not data.team_b:
        raise HTTPException(status_code=400, detail="Both team names are required")

    prompt = f"""
MATCH PREDICTION TASK

Team A: {data.team_a}
Team B: {data.team_b}

TASK:
1. Predict probabilities of Win/Draw/Loss for Team A
2. Suggest possible scoring outcomes (first goal, total goals)
3. Explain reasoning clearly in bullet points
4. Mention assumptions made if real-time data is not available
"""

    try:
        response = model.generate_content(prompt)
        return {
            "match": f"{data.team_a} vs {data.team_b}",
            "prediction": response.text,
            "disclaimer": "This prediction is AI-generated and based on general football knowledge. Not guaranteed."
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "AI failed to generate a prediction."
        }

# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000, 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
