import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os

# -----------------------------
# GEMINI CONFIG
# -----------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in environment")

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
app = FastAPI(title="Football Match Prediction Engine ⚽ (OpenLigaDB)")

# -----------------------------
# REQUEST MODEL
# -----------------------------
class MatchRequest(BaseModel):
    team_a: str
    team_b: str
    league_shortcut: str = "bl1"  # Default Bundesliga 1

# -----------------------------
# OPENLIGADB HELPERS
# -----------------------------
BASE_URL = "https://www.openligadb.de/api"

def get_teams(league_shortcut: str):
    url = f"{BASE_URL}/getavailableteams/{league_shortcut}/2026"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return []

def get_team_id(team_name: str, teams_list: list):
    # Case-insensitive match
    for t in teams_list:
        if t["TeamName"].lower() == team_name.lower():
            return t["TeamId"], t["TeamName"]
    return None, None

def get_matches(league_shortcut: str):
    url = f"{BASE_URL}/getmatchdata/{league_shortcut}/2026"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception:
        return []

def calculate_form(team_id: int, matches: list):
    form = {"W": 0, "D": 0, "L": 0}
    last5 = [m for m in matches if m["MatchIsFinished"]][:5]

    for m in last5:
        home_id = m["Team1"]["TeamId"]
        away_id = m["Team2"]["TeamId"]
        hs = m["MatchResults"][0]["PointsTeam1"]
        as_ = m["MatchResults"][0]["PointsTeam2"]

        if team_id == home_id:
            if hs > as_:
                form["W"] += 1
            elif hs == as_:
                form["D"] += 1
            else:
                form["L"] += 1
        elif team_id == away_id:
            if as_ > hs:
                form["W"] += 1
            elif as_ == hs:
                form["D"] += 1
            else:
                form["L"] += 1
    return form

# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.get("/")
def home():
    return {"status": "Football Match Predictor (OpenLigaDB) is running ⚽"}

@app.post("/predict")
def predict_match(data: MatchRequest):
    teams_list = get_teams(data.league_shortcut)
    if not teams_list:
        raise HTTPException(status_code=500, detail="Could not fetch teams from OpenLigaDB")

    # Get team IDs
    team_a_id, team_a_name = get_team_id(data.team_a, teams_list)
    team_b_id, team_b_name = get_team_id(data.team_b, teams_list)

    if not team_a_id or not team_b_id:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    # Get all matches in league
    all_matches = get_matches(data.league_shortcut)

    # Calculate form
    team_a_form = calculate_form(team_a_id, all_matches)
    team_b_form = calculate_form(team_b_id, all_matches)

    # Prepare AI prompt
    prompt = f"""
MATCH ANALYSIS DATA

TEAM A: Name: {team_a_name}, Recent Form (last 5 matches): {team_a_form}
TEAM B: Name: {team_b_name}, Recent Form (last 5 matches): {team_b_form}

TASK:
1. Predict Win/Draw/Loss probabilities
2. Suggest possible goal outcomes
3. Explain reasoning clearly in bullet points
"""

    # Call Gemini AI
    try:
        ai_response = model.generate_content(prompt)
        ai_text = ai_response.text
    except Exception:
        ai_text = "Prediction temporarily unavailable. Please try again later."

    return {
        "match": f"{team_a_name} vs {team_b_name}",
        "prediction": ai_text,
        "disclaimer": "This is an analytical prediction based on recent stats. No guarantees."
    }

# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
