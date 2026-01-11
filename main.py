import os
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware

# -------------------------------------------------
# 1. API CONFIGURATION
# Set your API Keys in Render/Environment Variables as GEMINI_API_KEY1, GEMINI_API_KEY2, GEMINI_API_KEY3
GEMINI_API_KEYS = [
    os.environ.get("GEMINI_API_KEY1"),
    os.environ.get("GEMINI_API_KEY2"),
    os.environ.get("GEMINI_API_KEY3")
]

# Filter out None or empty keys
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

if not GEMINI_API_KEYS:
    print("CRITICAL: No GEMINI_API_KEYS found! Set them in Render Dashboard.")

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
IDENTITY & ROLE
- You are 'AI Match Predictor'.
- Predict football match outcomes based on general knowledge of teams.
- NEVER mention model, developer, or API.

PREDICTION STYLE
- Provide a simple, short, clear comparison.
- Use a **Markdown table** to compare the two teams on key points (form, attack, defense, home/away strength).
- Bold the predicted result (e.g., **Win**, **Draw**, **Both Teams to Score**).
- Keep explanations minimal: 1-2 short factual points per team.
- Do NOT write long paragraphs or unnecessary details.
- Keep output light, smart, clear, and easy to read.

OUTPUT STRUCTURE
1. Table comparing the two teams.
2. Bolded prediction result.
3. Short reason(s) in bullets (1-3 lines max).
4. Avoid disclaimers unless explicitly asked.
"""

# -------------------------------------------------
# 3. INITIALIZE MODEL (Updated to working Gemini model)
def get_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
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

    # Shuffle the keys for random selection
    api_keys = GEMINI_API_KEYS.copy()
    random.shuffle(api_keys)
    
    last_error = None
    for api_key in api_keys:
        try:
            model = get_model(api_key)
            # Generate prediction using Gemini
            response = model.generate_content(prompt)
            return {
                "match": f"{input_data.team_a} vs {input_data.team_b}",
                "prediction": response.text,
                "disclaimer": "This prediction is AI-generated based on general football knowledge. Not guaranteed."
            }
        except Exception as e:
            last_error = str(e)
            if "429" in last_error:
                # Rate limit, try next key
                continue
            else:
                # Other error, but still try next
                continue
    
    # If all keys fail
    if "429" in last_error:
        return {
            "prediction": "All AI keys are currently rate-limited. Please wait a few seconds and try again.",
            "error": last_error
        }
    return {
        "prediction": "AI failed to generate a prediction with all available keys.",
        "error": last_error
    }

# -------------------------------------------------
# 6. RUN SERVER
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
