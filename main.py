import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------
load_dotenv()

SPORTDB_API_KEY = os.getenv("SPORTDB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not SPORTDB_API_KEY:
    raise RuntimeError("SPORTDB_API_KEY missing in .env")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")

# -----------------------------
# CONFIGURE GEMINI
# -----------------------------
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Identity: Football Match Prediction Analyst
Role: Analyze provided football statistics and predict match outcomes.
Rules:
- NEVER guarantee outcomes
- Use probabilities (%)
- Explain reasoning clearly
- Base conclusions ONLY on the data given
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# -----------------------------
# FASTAPI APP
# -----------------------------
app = FastAPI(title="Football Match Prediction Engine ⚽")

# -----------------------------
# REQUEST MODEL
# -----------------------------
class MatchRequest(BaseModel):
    team_a: str
    team_b: str

# -----------------------------
# SPORTDB HELPER FUNCTIONS
# -----------------------------
BASE_URL = "https://www.thesportsdb.com/api/v1/json"

def get_team(team_name: str):
    try:
        url = f"{BASE_URL}/{SPORTDB_API_KEY}/searchteams.php"
        r = requests.get(url, params={"t": team_name}, timeout=10)
        data = r.json()
        if not data or not data.get("teams"):
            return None
        return data["teams"][0]
    except Exception:
        return None

def get_last_matches(team_id: str):
    try:
        url = f"{BASE_URL}/{SPORTDB_API_KEY}/eventslast.php"
        r = requests.get(url, params={"id": team_id}, timeout=10)
        return r.json().get("results", []) or []
    except Exception:
        return []

def calculate_form(matches, team_name):
    form = {"W": 0, "D": 0, "L": 0}
    for m in matches[:5]:
        try:
            if m["intHomeScore"] is None or m["intAwayScore"] is None:
                continue
            hs = int(m["intHomeScore"])
            as_ = int(m["intAwayScore"])
            home = m["strHomeTeam"]
            away = m["strAwayTeam"]

            if team_name == home:
                if hs > as_:
                    form["W"] += 1
                elif hs == as_:
                    form["D"] += 1
                else:
                    form["L"] += 1
            elif team_name == away:
                if as_ > hs:
                    form["W"] += 1
                elif as_ == hs:
                    form["D"] += 1
                else:
                    form["L"] += 1
        except Exception:
            continue
    return form

# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.get("/")
def home():
    return {"status": "Football Match Predictor is running ⚽"}

@app.post("/predict")
def predict_match(data: MatchRequest):
    # GET TEAMS
    team_a = get_team(data.team_a)
    team_b = get_team(data.team_b)
    if not team_a or not team_b:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    # GET LAST MATCHES
    team_a_matches = get_last_matches(team_a["idTeam"])
    team_b_matches = get_last_matches(team_b["idTeam"])

    # PREPARE TEAM DATA
    team_a_data = {
        "name": team_a["strTeam"],
        "league": team_a.get("strLeague", "Unknown"),
        "stadium": team_a.get("strStadium", "Unknown"),
        "form": calculate_form(team_a_matches, team_a["strTeam"])
    }
    team_b_data = {
        "name": team_b["strTeam"],
        "league": team_b.get("strLeague", "Unknown"),
        "stadium": team_b.get("strStadium", "Unknown"),
        "form": calculate_form(team_b_matches, team_b["strTeam"])
    }

    # PREPARE PROMPT FOR AI
    prompt = f"""
MATCH ANALYSIS DATA

TEAM A: {team_a_data}
TEAM B: {team_b_data}

TASK:
1. Predict Win/Draw/Loss probabilities
2. Suggest possible goal outcomes
3. Explain reasoning clearly in bullet points
"""

    # CALL GEMINI AI
    try:
        ai_response = model.generate_content(prompt)
        ai_text = ai_response.text
    except Exception:
        ai_text = "Prediction temporarily unavailable. Please try again later."

    # RETURN RESPONSE
    return {
        "match": f"{team_a_data['name']} vs {team_b_data['name']}",
        "prediction": ai_text,
        "disclaimer": "This is an analytical prediction based on recent stats. No guarantees."
    }

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000)) if os.getenv("PORT") else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)
