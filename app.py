# app.py
# Final Unified application for the main tournament and the seeding tournament.
# Corrected score handling for Swiss format advance.

from flask import Flask, render_template, request, jsonify
import math
import json
import os
import copy
import requests
from datetime import datetime

# Nadeo API Configuration (Official Trackmania API)
NADEO_API_BASE = "https://api.trackmania.com"
NADEO_CLIENT_ID = None  # Will be set via environment variable or config
NADEO_CLIENT_SECRET = None  # Will be set via environment variable or config
NADEO_ACCESS_TOKEN = None  # Will be obtained via OAuth2 flow

# Load Nadeo credentials
def load_nadeo_credentials():
    """Load Nadeo API credentials from config file"""
    global NADEO_CLIENT_ID, NADEO_CLIENT_SECRET
    
    try:
        if os.path.exists('nadeo_config.json'):
            with open('nadeo_config.json', 'r') as f:
                config = json.load(f)
                NADEO_CLIENT_ID = config.get('nadeo_client_id')
                NADEO_CLIENT_SECRET = config.get('nadeo_client_secret')
                
                if NADEO_CLIENT_ID and NADEO_CLIENT_SECRET and NADEO_CLIENT_ID != "YOUR_NADEO_CLIENT_ID_HERE":
                    print("✅ Nadeo API credentials loaded successfully")
                    return True
                else:
                    print("⚠️  Nadeo API credentials not configured. Using mock data.")
                    return False
        else:
            print("⚠️  nadeo_config.json not found. Using mock data.")
            return False
    except Exception as e:
        print(f"❌ Error loading Nadeo credentials: {e}")
        return False

# Nadeo API Headers
NADEO_HEADERS = {
    'User-Agent': 'Serotonin Tournament Software - Nadeo Integration',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Nadeo API Functions
def get_nadeo_player_by_username(username_or_id):
    """
    Search for a Trackmania player by username or ID using the official Nadeo API
    Returns player data including ID, username, and rankings
    """
    try:
        # Get access token
        access_token = get_nadeo_access_token()
        if not access_token:
            print("No Nadeo access token available")
            return create_mock_player(username_or_id)
        
        # First, try to get player directly by ID if it looks like an ID
        if len(username_or_id) >= 20 and username_or_id.replace('-', '').isalnum():
            print(f"🔍 Detected Trackmania ID format: {username_or_id}")
            # This looks like a Trackmania ID, try direct lookup
            player_url = f"{NADEO_API_BASE}/players/{username_or_id}"
            headers = {**NADEO_HEADERS, 'Authorization': f'Bearer {access_token}'}
            
            print(f"🔗 Attempting direct ID lookup: {player_url}")
            response = requests.get(player_url, headers=headers, timeout=10)
            print(f"📡 ID lookup response: {response.status_code}")
            
            if response.status_code == 200:
                player = response.json()
                print(f"✅ ID lookup successful: {player}")
                return {
                    "trackmania_id": username_or_id,  # Use the original ID
                    "trackmania_name": player.get("name") or player.get("displayName") or f"Player_{username_or_id[:8]}",
                    "display_bracket_name": player.get("displayName") or player.get("name") or f"Player_{username_or_id[:8]}",
                    "seed": None,
                    "rank": player.get("rank"),
                    "score": player.get("score"),
                    "zone": player.get("zone")
                }
            else:
                print(f"❌ ID lookup failed: {response.status_code} - {response.text}")
        else:
            print(f"🔍 Detected username format: {username_or_id}")
        
        # If not an ID or direct lookup failed, search by username
        search_url = f"{NADEO_API_BASE}/players/search"
        headers = {**NADEO_HEADERS, 'Authorization': f'Bearer {access_token}'}
        params = {"search": username_or_id}
        
        print(f"🔍 Attempting username search: {search_url}")
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        print(f"📡 Username search response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Username search results: {data}")
            if data and len(data) > 0:
                # Return the first (most relevant) result
                player = data[0]
                print(f"✅ Username search successful: {player}")
                return {
                    "trackmania_id": player.get("id") or player.get("accountId") or f"nadeo-{username_or_id.lower()}",
                    "trackmania_name": username_or_id,  # Use the original search term
                    "display_bracket_name": player.get("displayName") or player.get("name") or username_or_id,
                    "seed": None,  # Will be assigned based on ranking
                    "rank": player.get("rank"),
                    "score": player.get("score"),
                    "zone": player.get("zone")
                }
        
        # If player not found, create mock player
        print(f"Player not found in Nadeo API, creating mock player: {username_or_id}")
        return create_mock_player(username_or_id)
        
    except Exception as e:
        print(f"Error fetching Nadeo player data: {e}")
        return create_mock_player(username_or_id)

def get_nadeo_player_rankings(limit=100):
    """
    Get top Trackmania players by ranking
    Useful for auto-seeding tournaments
    """
    try:
        rankings_url = f"{TRACKMANIA_API_BASE}/rankings/players"
        params = {"limit": limit}
        
        response = requests.get(rankings_url, params=params, headers=TRACKMANIA_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            players = []
            for i, player in enumerate(data):
                players.append({
                    "trackmania_id": player.get("id"),
                    "trackmania_name": player.get("name"),
                    "display_bracket_name": player.get("name"),
                    "seed": i + 1,  # Rank-based seeding
                    "rank": player.get("rank"),
                    "score": player.get("score"),
                    "zone": player.get("zone")
                })
            return players
        # If API fails, return mock data for testing
        print("API failed, returning mock rankings for testing")
        mock_players = []
        for i in range(min(limit, 32)):
            mock_players.append({
                "trackmania_id": f"tm-mock-{i+1}",
                "trackmania_name": f"Mock Player {i+1}",
                "display_bracket_name": f"Mock Player {i+1}",
                "seed": i + 1,
                "rank": i + 1,
                "score": 1000 - i * 10,
                "zone": "Mock Zone"
            })
        return mock_players
        
    except Exception as e:
        print(f"Error fetching Trackmania rankings: {e}")
        # Return mock data for testing
        mock_players = []
        for i in range(min(limit, 32)):
            mock_players.append({
                "trackmania_id": f"tm-mock-{i+1}",
                "trackmania_name": f"Mock Player {i+1}",
                "display_bracket_name": f"Mock Player {i+1}",
                "seed": i + 1,
                "rank": i + 1,
                "score": 1000 - i * 10,
                "zone": "Mock Zone"
            })
        return mock_players

def search_nadeo_players(query, limit=10):
    """
    Search for multiple Trackmania players by partial username
    Returns list of matching players
    """
    try:
        # Try direct player lookup first
        player = get_trackmania_player_by_username(query)
        if player:
            return [player]
        
        # If direct lookup fails, try search API
        search_url = f"{TRACKMANIA_API_BASE}/search/player"
        params = {"search": query, "limit": limit}
        
        response = requests.get(search_url, params=params, headers=TRACKMANIA_HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            players = []
            for player in data:
                players.append({
                    "trackmania_id": player.get("id") or f"tm-{player.get('name', query).lower()}",
                    "trackmania_name": player.get("name") or query,
                    "display_bracket_name": player.get("name") or query,
                    "seed": None,
                    "rank": player.get("rank"),
                    "score": player.get("score"),
                    "zone": player.get("zone")
                })
            return players
        # If all else fails, return mock player
        print(f"Search failed, returning mock player: {query}")
        return [{
            "trackmania_id": f"tm-{query.lower()}",
            "trackmania_name": query,
            "display_bracket_name": query,
            "seed": None,
            "rank": None,
            "score": None,
            "zone": None
        }]
    except Exception as e:
        print(f"Error searching Trackmania players: {e}")
        # Return mock player for testing
        return [{
            "trackmania_id": f"tm-{query.lower()}",
            "trackmania_name": query,
            "display_bracket_name": query,
            "seed": None,
            "rank": None,
            "score": None,
            "zone": None
        }]

# New Nadeo API Functions
def get_nadeo_access_token():
    """
    Get Nadeo API access token via OAuth2 flow
    This is required for all Nadeo API calls
    """
    global NADEO_ACCESS_TOKEN
    
    if NADEO_ACCESS_TOKEN:
        return NADEO_ACCESS_TOKEN
    
    try:
        # OAuth2 token endpoint
        token_url = "https://api.trackmania.com/oauth/access_token"
        
        # Client credentials flow (for server-to-server)
        data = {
            'grant_type': 'client_credentials',
            'client_id': NADEO_CLIENT_ID,
            'client_secret': NADEO_CLIENT_SECRET
        }
        
        response = requests.post(token_url, data=data, headers=NADEO_HEADERS, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            NADEO_ACCESS_TOKEN = token_data.get('access_token')
            return NADEO_ACCESS_TOKEN
        else:
            print(f"Failed to get Nadeo access token: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error getting Nadeo access token: {e}")
        return None

def create_mock_player(username_or_id):
    """Create a mock player for testing when API is unavailable"""
    print(f"🔄 Creating mock player for: {username_or_id}")
    
    # If it looks like a Trackmania ID, use it as the ID and generate a username
    if len(username_or_id) >= 20 and username_or_id.replace('-', '').isalnum():
        # This is likely a Trackmania ID
        print(f"🆔 Creating mock player from ID: {username_or_id}")
        return {
            "trackmania_id": username_or_id,
            "trackmania_name": f"Player_{username_or_id[:8]}",  # Generate a readable username
            "display_bracket_name": f"Player_{username_or_id[:8]}",  # Use the generated username
            "seed": None,
            "rank": None,
            "score": None,
            "zone": None
        }
    else:
        # This is likely a username
        print(f"👤 Creating mock player from username: {username_or_id}")
        return {
            "trackmania_id": f"nadeo-{username_or_id.lower()}",
            "trackmania_name": username_or_id,
            "display_bracket_name": username_or_id,
            "seed": None,
            "rank": None,
            "score": None,
            "zone": None
        }

def create_mock_rankings(limit):
    """Create mock rankings for testing when API is unavailable"""
    mock_players = []
    for i in range(min(limit, 32)):
        mock_players.append({
            "trackmania_id": f"nadeo-mock-{i+1}",
            "trackmania_name": f"Mock Player {i+1}",
            "display_bracket_name": f"Mock Player {i+1}",
            "seed": i + 1,
            "rank": i + 1,
            "score": 1000 - i * 10,
            "zone": "Mock Zone"
        })
    return mock_players

def auto_seed_players_by_ranking(players):
    """
    Auto-seed players based on their Trackmania ranking
    Higher ranked players get lower seed numbers
    """
    try:
        # Sort players by rank (lower rank = higher skill = lower seed)
        sorted_players = sorted(players, key=lambda p: p.get('rank', 999999))
        
        # Assign seeds based on ranking
        for i, player in enumerate(sorted_players):
            player['seed'] = i + 1
        
        return sorted_players
    except Exception as e:
        print(f"Error auto-seeding players: {e}")
        return players

app = Flask(__name__)

CONFIG_FILE = 'config.json'
SEEDING_CONFIG_FILE = 'seeding_config.json'

# Load Nadeo credentials on startup
load_nadeo_credentials()

# --- Configuration Management ---

def load_config(file, default_structure):
    if os.path.exists(file):
        with open(file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass 
    with open(file, 'w') as f:
        json.dump(default_structure, f, indent=4)
    return default_structure

def save_config(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

# --- In-memory database ---
db = {
    "main_tournament": {},
    "seeding_tournament": {}
}

# --- Load Main Tournament Config ---
default_main_config = {
    "players": [], "bracket": None, 
    "config": { "points_to_advance": 70, "points_for_finals": 100 }, 
    "info": { 
        "tournament_name": "Serotonin Tournament Software", "logo_url": "",
        "colors": { "text": "#f0f0f0", "background": "#000000" },
        "bracket_styles": {
            "upper": { "title": "UPPER BRACKET", "color": "#00FFFF" },
            "lower": { "title": "LOWER BRACKET", "color": "#FFA500" },
            "final": { "title": "GRAND FINAL", "color": "#FFD700" }
        }
    }, 
    "timer": { "minutes": 10, "font": "Orbitron", "color": "#8B5CF6", "position": "center" }, 
    "is_started": False, "bracket_type": "double_elimination"
}
db['main_tournament'] = load_config(CONFIG_FILE, default_main_config)
db['main_tournament']['is_started'] = False
db['main_tournament']['bracket'] = None
db['main_tournament']['players'] = []


# --- Load Seeding Tournament Config ---
default_seeding_config = {
    "players": [], "groups": { "groupA": [], "groupB": [] },
    "maps": ["Map 1", "Map 2", "Map 3"], "scores": {}, "is_started": False,
    "config": { 
        "players_to_advance": 8,
        "colors": {
            "header": "#6EE7B7",
            "text": "#F9FAFB",
            "score": "#34D399"
        }
    }
}
db['seeding_tournament'] = load_config(SEEDING_CONFIG_FILE, default_seeding_config)
db['seeding_tournament']['is_started'] = False


# --- Helper Functions ---

def create_serpentine_matches(players):
    num_players = len(players)
    if num_players == 0: return []
    num_matches = math.ceil(num_players / 4.0)
    padded_players = players + [{"trackmania_id": "BYE", "trackmania_name": "BYE", "display_bracket_name": "BYE", "seed": None}] * (int(num_matches) * 4 - num_players)
    matches = []
    for i in range(int(num_matches)):
        match_players = [
            padded_players[i],
            padded_players[int(num_matches) * 2 - 1 - i],
            padded_players[int(num_matches) * 2 + i],
            padded_players[int(num_matches) * 4 - 1 - i]
        ]
        matches.append([p for p in match_players if p['trackmania_id'] != "BYE"])
    return matches

def generate_double_elim_bracket(players):
    if not players: return None
    sorted_players = sorted(players, key=lambda p: p['seed'])
    bracket = {"upper": {"rounds": []}, "lower": {"rounds": []}, "grand_final": None}
    current_players = sorted_players
    round_num = 1
    while len(current_players) > 2:
        match_groups = create_serpentine_matches(current_players)
        matches = []
        for i, group in enumerate(match_groups):
            matches.append({"id": f"UB-R{round_num}M{i+1}", "players": [{"trackmania_id": p["trackmania_id"], "trackmania_name": p["trackmania_name"], "display_bracket_name": p["display_bracket_name"], "seed": p["seed"], "score": 0} for p in group], "winners": [], "is_complete": False})
        bracket["upper"]["rounds"].append({"name": f"Upper Round {round_num}", "matches": matches})
        num_winners = len(matches) * 2
        if num_winners <= 2: break
        current_players = [{"trackmania_id": "TBD", "trackmania_name": "TBD", "display_bracket_name": "TBD", "seed": None}] * num_winners
        round_num += 1
    num_ub_rounds = len(bracket["upper"]["rounds"])
    for i in range(num_ub_rounds + 1):
        num_matches = len(bracket["upper"]["rounds"][i]["matches"]) if i < num_ub_rounds else 1
        num_lb_matches = math.ceil(num_matches / 2.0)
        if num_lb_matches > 0:
            bracket["lower"]["rounds"].append({"name": f"Lower Round {i+1}", "matches": [{"id": f"LB-R{i+1}M{j+1}", "players": [{"trackmania_id": "TBD", "trackmania_name": "TBD", "display_bracket_name": "TBD", "seed": None, "score": 0} for _ in range(4)], "winners": [], "is_complete": False} for j in range(int(num_lb_matches))]})
    bracket["grand_final"] = {"name": "Grand Final", "matches": [{"id": "GF-M1", "players": [{"trackmania_id": "TBD", "trackmania_name": "TBD", "display_bracket_name": "TBD", "seed": None, "score": 0} for _ in range(4)], "winners": [], "is_complete": False}]}
    return bracket

def generate_swiss_bracket(players):
    if len(players) != 16: return None
    sorted_players = sorted(players, key=lambda p: p['seed'])
    matches = [
        {"id": "SWISS-R1-M1", "name": "Match 1", "players": [{"trackmania_id": p["trackmania_id"], "trackmania_name": p["trackmania_name"], "display_bracket_name": p["display_bracket_name"], "seed": p["seed"], "score": 0, "is_winner": False} for p in sorted_players if p['seed'] in [1,2,3,4]], "is_complete": False},
        {"id": "SWISS-R1-M2", "name": "Match 2", "players": [{"trackmania_id": p["trackmania_id"], "trackmania_name": p["trackmania_name"], "display_bracket_name": p["display_bracket_name"], "seed": p["seed"], "score": 0, "is_winner": False} for p in sorted_players if p['seed'] in [5,6,7,8]], "is_complete": False},
        {"id": "SWISS-R1-M3", "name": "Match 3", "players": [{"trackmania_id": p["trackmania_id"], "trackmania_name": p["trackmania_name"], "display_bracket_name": p["display_bracket_name"], "seed": p["seed"], "score": 0, "is_winner": False} for p in sorted_players if p['seed'] in [9,10,11,12]], "is_complete": False},
        {"id": "SWISS-R1-M4", "name": "Match 4", "players": [{"trackmania_id": p["trackmania_id"], "trackmania_name": p["trackmania_name"], "display_bracket_name": p["display_bracket_name"], "seed": p["seed"], "score": 0, "is_winner": False} for p in sorted_players if p['seed'] in [13,14,15,16]], "is_complete": False}
    ]
    return {"stage": "seeding", "matches": matches, "history": {}, "round": 1}

def advance_players(winners,losers,bracket_type,round_index,match_index):
    grand_final_match=db["main_tournament"]["bracket"]["grand_final"]["matches"][0]
    if bracket_type=='upper':
        next_ub_round_index=round_index+1
        if next_ub_round_index>=len(db["main_tournament"]["bracket"]["upper"]["rounds"]):
            grand_final_match["players"][0]=winners[0]
            grand_final_match["players"][1]=winners[1]
        else:
            next_match_index=match_index//2
            start_slot=(match_index%2)*2
            next_match=db["main_tournament"]["bracket"]["upper"]["rounds"][next_ub_round_index]["matches"][next_match_index]
            next_match["players"][start_slot]=winners[0]
            next_match["players"][start_slot+1]=winners[1]
        if round_index==0:
            lb_round_index=0
        else:
            lb_round_index=(round_index-1)*2+1
        if lb_round_index<len(db["main_tournament"]["bracket"]["lower"]["rounds"]):
            next_match_index=match_index//2
            start_slot=(match_index%2)*2
            next_match=db["main_tournament"]["bracket"]["lower"]["rounds"][lb_round_index]["matches"][next_match_index]
            next_match["players"][start_slot]=losers[0]
            next_match["players"][start_slot+1]=losers[1]
    elif bracket_type=='lower':
        next_lb_round_index=round_index+1
        if next_lb_round_index>=len(db["main_tournament"]["bracket"]["lower"]["rounds"]):
            grand_final_match["players"][2]=winners[0]
            grand_final_match["players"][3]=winners[1]
        else:
            next_match_index=match_index//2
            start_slot=(match_index%2)*2
            if next_match_index<len(db["main_tournament"]["bracket"]["lower"]["rounds"][next_lb_round_index]["matches"]):
                next_match=db["main_tournament"]["bracket"]["lower"]["rounds"][next_lb_round_index]["matches"][next_match_index]
                next_match["players"][start_slot]=winners[0]
                next_match["players"][start_slot+1]=winners[1]
    
    # Save the updated bracket state
    save_config(CONFIG_FILE, db['main_tournament'])

# --- Main Routes ---
@app.route('/')
def index(): return render_template('index.html')
@app.route('/stream')
def stream_view(): return render_template('stream.html')
@app.route('/featured')
def featured_view(): return render_template('featured.html')
@app.route('/timer')
def timer_view(): return render_template('timer.html')
@app.route('/seeding_graphic')
def seeding_graphic(): return render_template('seeding_graphic.html')

# --- Main API Endpoints ---
@app.route('/api/status', methods=['GET'])
def get_status(): return jsonify(db['main_tournament'])

@app.route('/api/stop', methods=['POST'])
def stop_tournament(): 
    db['main_tournament']['is_started'] = False
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify({"message": "Tournament stopped."})

@app.route('/api/update_timer', methods=['POST'])
def update_timer():
    data = request.get_json()
    for key in ['minutes', 'font', 'color', 'position']:
        if key in data: db['main_tournament']['timer'][key] = data[key]
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify(db['main_tournament']['timer'])

@app.route('/api/update_info', methods=['POST'])
def update_info():
    data = request.get_json()
    for key in ['tournament_name', 'featured_match', 'colors', 'logo_url', 'bracket_styles']:
        if key in data: db['main_tournament']['info'][key] = data[key]
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify(db['main_tournament']['info'])

@app.route('/api/reset', methods=['POST'])
def reset_tournament():
    db['main_tournament'] = default_main_config
    db['main_tournament']['is_started'] = False
    db['main_tournament']['bracket'] = None
    db['main_tournament']['players'] = []
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify({"message": "Tournament reset successfully."})

@app.route('/api/update_match', methods=['POST'])
def update_match():
    data=request.get_json()
    bracket_type=data.get('bracket_type')
    scores=data.get('scores')
    bracket = db['main_tournament']['bracket']
    config = db['main_tournament']['config']

    if bracket_type == 'swiss':
        match_id = data.get('match_id')
        match_to_update = next((m for m in bracket['matches'] if m['id'] == match_id), None)
        if match_to_update:
            for i, player in enumerate(match_to_update['players']):
                if i < len(scores):
                    player['score'] = scores[i]
            
            # Recalculate winner status after updating scores
            # Sort players by score, then by seed
            match_to_update['players'].sort(key=lambda p: (p.get('score', 0), -p['seed']), reverse=True)
            # Mark top 2 as winners
            for i, player in enumerate(match_to_update['players']):
                player['is_winner'] = (i < 2)
            
            save_config(CONFIG_FILE, db['main_tournament'])
        return jsonify(db['main_tournament'])

    round_index=data.get('round_index')
    match_index=data.get('match_index')
    try:
        if bracket_type=='grand_final':match=bracket["grand_final"]["matches"][match_index];points_needed=config["points_for_finals"]
        else:match=bracket[bracket_type]["rounds"][round_index]["matches"][match_index];points_needed=config["points_to_advance"]
        for i,player in enumerate(match["players"]):
            if i<len(scores):player["score"]=int(scores[i])
        players_with_scores=[p for p in match["players"]if p.get('trackmania_id')not in[None,"TBD","BYE"]];players_with_scores.sort(key=lambda p:p.get('score',0),reverse=True)
        qualified_players=[p for p in players_with_scores if p.get('score',0)>=points_needed]
        if len(qualified_players)>=2:
            winners=qualified_players[:2];match["winners"]=winners;match["is_complete"]=True
            if bracket_type!='grand_final':
                all_player_ids=[p['trackmania_id']for p in match['players']];winner_ids=[p['trackmania_id']for p in winners];loser_ids=[id for id in all_player_ids if id not in winner_ids and id not in["TBD","BYE"]];losers=[p for p in match['players']if p['trackmania_id']in loser_ids]
                advancing_winners=[{"trackmania_id":w["trackmania_id"],"trackmania_name":w["trackmania_name"],"display_bracket_name":w["display_bracket_name"],"seed":w["seed"],"score":0}for w in winners];advancing_losers=[{"trackmania_id":l["trackmania_id"],"trackmania_name":l["trackmania_name"],"display_bracket_name":l["display_bracket_name"],"seed":l["seed"],"score":0}for l in losers]
                advance_players(advancing_winners,advancing_losers,bracket_type,round_index,match_index)
        else:match["winners"]=[];match["is_complete"]=False
        save_config(CONFIG_FILE, db['main_tournament'])
    except(IndexError,TypeError,KeyError)as e:return jsonify({"error":f"Invalid data provided: {e}"}),400
    return jsonify(db['main_tournament'])

@app.route('/api/config', methods=['POST'])
def update_config():
    data=request.get_json()
    points=data.get('points_to_advance')
    final_points=data.get('points_for_finals')
    if points is not None:db["main_tournament"]["config"]["points_to_advance"]=int(points)
    if final_points is not None:db["main_tournament"]["config"]["points_for_finals"]=int(final_points)
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify(db["main_tournament"]["config"])

@app.route('/api/start', methods=['POST'])
def start_main_tournament():
    data=request.get_json();players=data.get('players',[])
    bracket_type = data.get('bracket_type', 'double_elimination')
    
    main_db = db["main_tournament"]
    # If players are already in the new format, use them directly
    if players and isinstance(players[0], dict) and 'trackmania_id' in players[0]:
        main_db["players"] = players
    else:
        # Fallback to old format for backward compatibility
        main_db["players"] = [{"trackmania_id": f"temp-id-{i+1}", "trackmania_name": name, "display_bracket_name": name, "seed": i + 1} for i, name in enumerate(players)]
    main_db["bracket_type"] = bracket_type

    if bracket_type == "double_elimination":
        main_db["bracket"] = generate_double_elim_bracket(main_db["players"])
    elif bracket_type == "swiss":
        if len(main_db["players"]) != 16:
            return jsonify({"error": "Swiss format requires exactly 16 players."}), 400
        main_db["bracket"] = generate_swiss_bracket(main_db["players"])

    main_db["is_started"] = True
    save_config(CONFIG_FILE, main_db)
    return jsonify(main_db)

# --- Seeding API Endpoints ---
@app.route('/api/seeding/status', methods=['GET'])
def get_seeding_status():
    return jsonify(db['seeding_tournament'])

@app.route('/api/seeding/start', methods=['POST'])
def start_seeding():
    data = request.get_json()
    players = data.get('players', [])
    maps = data.get('maps', [])
    
    seeding_db = db['seeding_tournament']
    seeding_db['players'] = players
    seeding_db['maps'] = maps
    seeding_db['scores'] = {player: {map_name: 0 for map_name in maps} for player in players}
    seeding_db['is_started'] = True
    
    midpoint = len(players) // 2
    seeding_db['groups']['groupA'] = players[:midpoint]
    seeding_db['groups']['groupB'] = players[midpoint:]

    save_config(SEEDING_CONFIG_FILE, seeding_db)
    return jsonify(seeding_db)

@app.route('/api/seeding/update_scores', methods=['POST'])
def update_seeding_scores():
    data = request.get_json()
    player = data.get('player')
    map_name = data.get('map_name')
    score = data.get('score')
    
    seeding_db = db['seeding_tournament']
    if player in seeding_db['scores'] and map_name in seeding_db['maps']:
        try:
            seeding_db['scores'][player][map_name] = int(score)
            save_config(SEEDING_CONFIG_FILE, seeding_db)
            return jsonify({"success": True})
        except (ValueError):
            return jsonify({"error": "Invalid score"}), 400
    
    return jsonify({"error": "Player or map not found"}), 404

@app.route('/api/seeding/reset', methods=['POST'])
def reset_seeding():
    db['seeding_tournament'] = default_seeding_config
    db['seeding_tournament']['is_started'] = False
    save_config(SEEDING_CONFIG_FILE, db['seeding_tournament'])
    return jsonify({"message": "Seeding tournament reset."})
    
@app.route('/api/seeding/update_config', methods=['POST'])
def update_seeding_config():
    data = request.get_json()
    if 'players_to_advance' in data:
        db['seeding_tournament']['config']['players_to_advance'] = int(data['players_to_advance'])
    if 'colors' in data:
        db['seeding_tournament']['config']['colors'] = data['colors']
    save_config(SEEDING_CONFIG_FILE, db['seeding_tournament'])
    return jsonify(db['seeding_tournament']['config'])

# Trackmania API Integration Endpoints
@app.route('/api/trackmania/search', methods=['POST'])
def search_trackmania_players():
    """
    Search for Trackmania players by username
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({"error": "Search query must be at least 2 characters"}), 400
        
        players = search_nadeo_players(query, limit=10)
        return jsonify({
            "success": True,
            "players": players,
            "query": query
        })
    except Exception as e:
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

@app.route('/api/trackmania/player/<username>')
def get_trackmania_player(username):
    """
    Get detailed information for a specific Trackmania player
    """
    try:
        player = get_nadeo_player_by_username(username)
        if player:
            return jsonify({
                "success": True,
                "player": player
            })
        else:
            return jsonify({
                "success": False,
                "error": "Player not found"
            }), 404
    except Exception as e:
        return jsonify({"error": f"Failed to fetch player: {str(e)}"}), 500

@app.route('/api/trackmania/rankings')
def get_trackmania_rankings():
    """
    Get top Trackmania players for auto-seeding
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        if limit > 200:  # Prevent abuse
            limit = 200
        
        players = get_nadeo_player_rankings(limit)
        return jsonify({
            "success": True,
            "players": players,
            "count": len(players)
        })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch rankings: {str(e)}"}), 500

@app.route('/api/trackmania/test', methods=['GET'])
def test_trackmania_api():
    """
    Test endpoint to verify Trackmania API connectivity
    """
    try:
        # Test a simple API call
        test_url = f"{NADEO_API_BASE}/players/search"
        params = {"search": "test"}
        
        # Get access token first
        access_token = get_nadeo_access_token()
        if not access_token:
            return jsonify({
                "success": False,
                "error": "No Nadeo access token available. Please configure CLIENT_ID and CLIENT_SECRET.",
                "api_working": False
            }), 500
        
        headers = {**NADEO_HEADERS, 'Authorization': f'Bearer {access_token}'}
        response = requests.get(test_url, params=params, headers=headers, timeout=10)
        
        return jsonify({
            "success": True,
            "status_code": response.status_code,
            "api_working": response.status_code == 200,
            "response_preview": response.text[:200] if response.status_code == 200 else "API Error",
            "headers_sent": headers,
            "api_base": NADEO_API_BASE,
            "has_access_token": bool(access_token)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "api_working": False
        }), 500

@app.route('/api/trackmania/test-player/<query>', methods=['GET'])
def test_player_lookup(query):
    """
    Test endpoint to debug player lookup logic
    """
    try:
        print(f"🧪 Testing player lookup for: {query}")
        
        # Test the player lookup function
        player = get_nadeo_player_by_username(query)
        
        # Determine if it was treated as ID or username
        is_id_format = len(query) >= 20 and query.replace('-', '').isalnum()
        
        return jsonify({
            "success": True,
            "query": query,
            "treated_as": "ID" if is_id_format else "Username",
            "result": player,
            "debug_info": {
                "query_length": len(query),
                "is_alphanumeric_with_dashes": query.replace('-', '').isalnum(),
                "is_id_format": is_id_format
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "debug_info": {
                "query": query,
                "query_length": len(query) if query else 0
            }
        }), 500

@app.route('/api/trackmania/auto-seed', methods=['POST'])
def auto_seed_tournament():
    """
    Auto-seed a tournament using Trackmania rankings
    """
    try:
        data = request.get_json()
        player_count = data.get('player_count', 16)
        use_rankings = data.get('use_rankings', True)
        
        if player_count > 200:
            return jsonify({"error": "Maximum 200 players allowed"}), 400
        
        if use_rankings:
            # Get top players by ranking
            players = get_nadeo_player_rankings(player_count)
            # Auto-seed based on ranking
            players = auto_seed_players_by_ranking(players)
        else:
            # Just get players without auto-seeding
            players = get_nadeo_player_rankings(player_count)
        
        return jsonify({
            "success": True,
            "players": players,
            "count": len(players),
            "auto_seeded": use_rankings
        })
    except Exception as e:
        return jsonify({"error": f"Auto-seeding failed: {str(e)}"}), 500

@app.route('/api/advance_swiss_stage', methods=['POST'])
def advance_swiss_stage():
    bracket = db["main_tournament"]['bracket']
    if not bracket or db["main_tournament"].get('bracket_type') != 'swiss':
        return jsonify({"error": "Invalid state for this action"}), 400
    
    bracket['history'][f"round_{bracket['round']}"] = copy.deepcopy(bracket['matches'])

    if bracket['round'] == 1:
        # Mark winners in current round before advancing
        for match in bracket['matches']:
            # Sort players by score, then by seed
            match['players'].sort(key=lambda p: (p.get('score', 0), -p['seed']), reverse=True)
            # Mark top 2 as winners
            for i, player in enumerate(match['players']):
                player['is_winner'] = (i < 2)
        
        all_players = []
        for match in bracket['matches']:
            all_players.extend(sorted(match['players'], key=lambda p: p.get('score', 0), reverse=True))
        
        top_8 = all_players[:8]
        bottom_8 = all_players[8:]

        # Create new matches and preserve winner status
        new_matches = [
            {"id": "SWISS-R2-M1", "name": "Top 8 - Match 1", "players": top_8[:4]},
            {"id": "SWISS-R2-M2", "name": "Top 8 - Match 2", "players": top_8[4:]},
            {"id": "SWISS-R2-M3", "name": "Bottom 8 - Match 1", "players": bottom_8[:4]},
            {"id": "SWISS-R2-M4", "name": "Bottom 8 - Match 2", "players": bottom_8[4:]}
        ]
        
        # Ensure all players have is_winner field (default to false for new matches)
        for match in new_matches:
            for player in match['players']:
                if 'is_winner' not in player:
                    player['is_winner'] = False
        
        bracket['matches'] = new_matches
        bracket['round'] = 2

    elif bracket['round'] == 2:
        # Mark winners in current round before advancing
        for match in bracket['matches']:
            # Sort players by score, then by seed
            match['players'].sort(key=lambda p: (p.get('score', 0), -p['seed']), reverse=True)
            # Mark top 2 as winners
            for i, player in enumerate(match['players']):
                player['is_winner'] = (i < 2)
        
        # For round 2, use only the current round scores to determine seeding
        all_players = []
        for match in bracket['matches']:
            all_players.extend(sorted(match['players'], key=lambda p: p.get('score', 0), reverse=True))
        
        # Sort by current round performance, then by seed
        final_seeding = sorted(all_players, key=lambda p: (p.get('score', 0), -p['seed']), reverse=True)

        bracket['stage'] = 'groups'
        # Create new matches and preserve winner status
        new_matches = [
            {"id": "champion", "name": "Champion", "players": final_seeding[0:4]},
            {"id": "gold", "name": "Gold", "players": final_seeding[4:8]},
            {"id": "silver", "name": "Silver", "players": final_seeding[8:12]},
            {"id": "bronze", "name": "Bronze", "players": final_seeding[12:16]}
        ]
        
        # Ensure all players have is_winner field (default to false for new matches)
        for match in new_matches:
            for player in match['players']:
                if 'is_winner' not in player:
                    player['is_winner'] = False
        
        bracket['matches'] = new_matches
        bracket['round'] = 3
    
    elif bracket['round'] in [3, 4]:
        groups = {g['id']: g for g in bracket['matches']}
        
        # For each group, determine winners based on current round performance only
        for group in groups.values():
            # Sort players by current round score first, then by seed (higher seed = lower number = higher priority)
            group['players'].sort(key=lambda p: (
                p.get('score', 0),  # Current round score (highest first)
                -p['seed']  # Seed (higher seed = lower number = higher priority)
            ), reverse=True)
            
            # Mark top 2 players as winners for this round
            for i, player in enumerate(group['players']):
                player['is_winner'] = (i < 2)

        # For round 3 specifically, ensure gold match prioritizes higher seeds when scores are tied
        if bracket['round'] == 3:
            # Sort champion group bottom 2 and silver group top 2 by seed when creating gold match
            champion_bottom = sorted(groups['champion']['players'][2:], key=lambda p: p['seed'])
            silver_top = sorted(groups['silver']['players'][:2], key=lambda p: p['seed'])
            new_gold = champion_bottom + silver_top
        else:
            new_gold = groups['champion']['players'][2:] + groups['silver']['players'][:2]

        new_champion = groups['champion']['players'][:2] + groups['gold']['players'][:2]
        new_silver = groups['silver']['players'][2:] + groups['bronze']['players'][:2]
        new_bronze = groups['bronze']['players'][2:]

        # Create new matches and ensure all players have is_winner field
        new_matches = [
            {"id": "champion", "name": "Champion", "players": new_champion},
            {"id": "gold", "name": "Gold", "players": new_gold},
            {"id": "silver", "name": "Silver", "players": new_silver},
            {"id": "bronze", "name": "Bronze", "players": new_bronze}
        ]
        
        # Ensure all players have is_winner field (default to false for new matches)
        for match in new_matches:
            for player in match['players']:
                if 'is_winner' not in player:
                    player['is_winner'] = False
        
        bracket['matches'] = new_matches
        bracket['round'] += 1

    # Reset scores for new round
    for match in bracket['matches']:
        for player in match['players']: 
            player['score'] = 0

    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify(db['main_tournament'])

@app.route('/api/go_back_swiss', methods=['POST'])
def go_back_swiss():
    bracket = db["main_tournament"]['bracket']
    if not bracket or db["main_tournament"].get('bracket_type') != 'swiss':
        return jsonify({"error": "Invalid state for this action"}), 400
    
    if bracket['round'] <= 1:
        return jsonify({"error": "Cannot go back from round 1"}), 400
    
    # Get the previous round from history
    prev_round_key = f"round_{bracket['round'] - 1}"
    if prev_round_key not in bracket['history']:
        return jsonify({"error": "Previous round data not found"}), 400
    
    # Restore the previous round
    bracket['matches'] = copy.deepcopy(bracket['history'][prev_round_key])
    bracket['round'] -= 1
    
    # Remove the current round from history since we're going back
    current_round_key = f"round_{bracket['round']}"
    if current_round_key in bracket['history']:
        del bracket['history'][current_round_key]
    
    # Reset scores for the restored round and ensure is_winner field exists
    for match in bracket['matches']:
        for player in match['players']: 
            player['score'] = 0
            if 'is_winner' not in player:
                player['is_winner'] = False
    
    save_config(CONFIG_FILE, db['main_tournament'])
    return jsonify(db['main_tournament'])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
