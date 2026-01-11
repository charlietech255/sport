import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai

# -------------------------------------------------
# ENV SETUP
# -------------------------------------------------
load_dotenv()

SPORTDB_API_KEY = os.getenv("SPORTDB_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not SPORTDB_API_KEY:
    raise RuntimeError("SPORTDB_API_KEY missing")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

# -------------------------------------------------
# GEMINI CONFIG
# -------------------------------------------------
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

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
app = FastAPI(title="Match Prediction Engine ⚽")

# -------------------------------------------------
# REQUEST MODEL
# -------------------------------------------------
class MatchRequest(BaseModel):
    team_a: str
    team_b: str

# -------------------------------------------------
# SPORTDB HELPERS
# -------------------------------------------------
BASE_URL = "https://www.thesportsdb.com/api/v1/json"

def get_team(team_name: str):
    url = f"{BASE_URL}/{SPORTDB_API_KEY}/searchteams.php"
    r = requests.get(url, params={"t": team_name}, timeout=10)
    data = r.json()
    if not data or not data.get("teams"):
        return None
    return data["teams"][0]

def get_last_matches(team_id: str):
    url = f"{BASE_URL}/{SPORTDB_API_KEY}/eventslast.php"
    r = requests.get(url, params={"id": team_id}, timeout=10)
    return r.json().get("results", [])

def calculate_form(matches, team_name):
    form = {"W": 0, "D": 0, "L": 0}
    for m in matches[:5]:
        hs, as_ = int(m["intHomeScore"]), int(m["intAwayScore"])
        home, away = m["strHomeTeam"], m["strAwayTeam"]

        if team_name == home:
            form["W" if hs > as_ else "D" if hs == as_ else "L"] += 1
        elif team_name == away:
            form["W" if as_ > hs else "D" if hs == as_ else "L"] += 1
    return form

# -------------------------------------------------
# API ROUTES
# -------------------------------------------------
@app.get("/")
def home():
    return {"status": "Match Predictor is running ⚽"}

@app.post("/predict")
def predict_match(data: MatchRequest):
    team_a = get_team(data.team_a)
    team_b = get_team(data.team_b)

    if not team_a or not team_b:
        raise HTTPException(status_code=404, detail="One or both teams not found")

    team_a_matches = get_last_matches(team_a["idTeam"])
    team_b_matches = get_last_matches(team_b["idTeam"])

    team_a_data = {
        "name": team_a["strTeam"],
        "league": team_a["strLeague"],
        "stadium": team_a["strStadium"],
        "form": calculate_form(team_a_matches, team_a["strTeam"])
    }

    team_b_data = {
        "name": team_b["strTeam"],
        "league": team_b["strLeague"],
        "stadium": team_b["strStadium"],
        "form": calculate_form(team_b_matches, team_b["strTeam"])
    }

    prompt = f"""
MATCH ANALYSIS DATA

TEAM A:
Name: {team_a_data['name']}
League: {team_a_data['league']}
Recent Form (last 5): {team_a_data['form']}
Stadium: {team_a_data['stadium']}

TEAM B:
Name: {team_b_data['name']}
League: {team_b_data['league']}
Recent Form (last 5): {team_b_data['form']}
Stadium: {team_b_data['stadium']}

TASK:
1. Predict Win/Draw/Loss probabilities
2. Suggest possible goal outcomes
3. Explain reasons clearly in bullet points
"""

    ai_response = model.generate_content(prompt)

    return {
        "match": f"{team_a_data['name']} vs {team_b_data['name']}",
        "prediction": ai_response.text,
        "disclaimer": "This is an analytical prediction, not a guarantee."
    }

# -------------------------------------------------
# RUN SERVER
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
