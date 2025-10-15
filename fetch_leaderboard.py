import requests
import json
import time
import os

class Run:
    def __init__(self, name, frames, map_name, rank):
        self.name = name
        self.frames = frames
        self.map_name = map_name
        self.rank = rank

# --------------------
# CONFIG
# --------------------
USER_JSON_FILE = "user_ids.json"
VERSION = "0.5.1"
DELAY_BETWEEN_REQUESTS = 1.0
MAX_RANK = 20000
TRACKS_PER_RUN = 4
LAST_TRACK_FILE = "last_track.json"

# --------------------
# Community Tracks
# --------------------
COMMUNITY_TRACKS = [
    ("92bb4c33f5d1f8baf684dc214f0f321967c92dab87726ab0aba27cea9dbd8734", "1"),
    ("8103eafa75228d2db501bb2995deca1a9a4f29d45ee50c221dd5ccbcaefd7a72", "2"),
    ("3f7c652ae4a0804012a4415a515aef803b806ac750aad5c579a4fddd2aea6c52", "3"),
    ("8c8f09a092f13b46a4f60b1175c8b6f7eb56e72e55802463ff90d8b0c5a6223f", "4"),
    ("19d9532f837b4e639fb4474ba3c198d26e0fba23ed95bd7bb8b6c6db359ef4f3", "5"),
    ("8091591f45280c361e6a4fd126566e3b9a99e47c86776278554512c78b00bb0a", "6")
]

TRACKS = COMMUNITY_TRACKS
track_style = "Community"

# --------------------
# Load player data
# --------------------
if not os.path.exists(USER_JSON_FILE):
    print(f"Error: {USER_JSON_FILE} not found!")
    exit(1)

with open(USER_JSON_FILE, "r") as f:
    user_ids = json.load(f)

hash_to_name = {info["hash"]: name for name, info in user_ids.items()}

# --------------------
# Load last track index
# --------------------
if os.path.exists(LAST_TRACK_FILE):
    with open(LAST_TRACK_FILE) as f:
        last_index = json.load(f).get("index", 0)
else:
    last_index = 0

# --------------------
# Load existing leaderboard
# --------------------
if os.path.exists("leaderboard.json"):
    with open("leaderboard.json", "r") as f:
        output_data = json.load(f)
else:
    output_data = {"players": [], "tracks": []}

# --------------------
# Select tracks to update
# --------------------
tracks_to_update = TRACKS[last_index:last_index + TRACKS_PER_RUN]
if len(tracks_to_update) < TRACKS_PER_RUN:  # wrap around
    tracks_to_update += TRACKS[:TRACKS_PER_RUN - len(tracks_to_update)]

# --------------------
# Fetch leaderboard entries
# --------------------
def fetch_track_entries(track_id, player_hashes, max_rank=MAX_RANK):
    skip = 0
    amount = 500
    found_entries = {}
    while skip < max_rank:
        url = f"https://vps.kodub.com/leaderboard?version={VERSION}&trackId={track_id}&skip={skip}&amount={amount}&onlyVerified=true"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            entries = data.get("entries", [])
            total = data.get("total", 0)

            for i, entry in enumerate(entries):
                uid = entry.get("userId")
                if uid in player_hashes:
                    entry["position"] = skip + i + 1
                    found_entries[uid] = entry

            if not entries or skip + amount >= total:
                break

            skip += amount
            time.sleep(DELAY_BETWEEN_REQUESTS)
        except Exception as e:
            print(f"Error fetching {track_id}: {e}")
            break
    return found_entries

# --------------------
# Update JSON if needed
# --------------------
def update_user_json(user_ids, filename=USER_JSON_FILE):
    with open(filename, "w") as f:
        json.dump(user_ids, f, indent=2)
    print(f"✅ Updated {filename}")

# --------------------
# Process selected tracks
# --------------------
all_runs = []

for track_id, track_name in tracks_to_update:
    print(f"\n=== Fetching {track_name} ===")
    found_entries = fetch_track_entries(track_id, set(hash_to_name.keys()))

    for uid, entry in found_entries.items():
        stored_name = hash_to_name[uid]
        stored_colors = user_ids[stored_name].get("carColors", [])
        actual_name = entry.get("name", stored_name)
        frames = entry.get("frames", 0)
        rank = entry.get("position", None)

        # Parse colors
        actual_colors = stored_colors
        car_colors_hex = entry.get("carColors", "")
        if car_colors_hex and len(car_colors_hex) % 6 == 0:
            actual_colors = [car_colors_hex[i:i+6] for i in range(0, len(car_colors_hex), 6)]

        # Update user_ids.json if name/colors changed
        if stored_name != actual_name or stored_colors != actual_colors:
            user_ids.pop(stored_name)
            user_ids[actual_name] = {"hash": uid, "carColors": actual_colors}
            update_user_json(user_ids)
            hash_to_name[uid] = actual_name

        all_runs.append(Run(actual_name, frames, track_name, rank))
        print(f"{actual_name:20} {rank!s:>6} {frames/1000:.3f}s")

    # Players without record
    for uid, stored_name in hash_to_name.items():
        if uid not in found_entries:
            all_runs.append(Run(stored_name, 0, track_name, None))
            print(f"{stored_name:20} {'No record':>6}")

# --------------------
# Update track stats in existing leaderboard
# --------------------
for track_id, track_name in tracks_to_update:
    track_results = []
    for player, info in user_ids.items():
        run_for_map = next((r for r in all_runs if r.name == player and r.map_name == track_name), None)
        if run_for_map and run_for_map.rank is not None:
            track_results.append({
                "player": player,
                "time": round(run_for_map.frames / 1000.0, 3),
                "rank": run_for_map.rank
            })
        else:
            track_results.append({"player": player, "time": None, "rank": None})

    # Replace old track data or add new
    existing = next((t for t in output_data["tracks"] if t["name"] == track_name), None)
    if existing:
        existing["results"] = track_results
    else:
        output_data["tracks"].append({"name": track_name, "results": track_results})

# --------------------
# Update player stats
# --------------------

# 1️⃣ Schlechteste Zeit pro Track sammeln (aus allen Tracks!)
worst_time_per_track = {}
for track in output_data["tracks"]:
    times = [res["time"] for res in track["results"] if res["time"] is not None]
    if times:
        worst_time_per_track[track["name"]] = max(times)

# 2️⃣ Spielerstatistiken neu berechnen
output_data["players"] = []
for player, info in user_ids.items():
    total_time = 0.0
    ranks = []

    for track in output_data["tracks"]:
        result = next((r for r in track["results"] if r["player"] == player), None)
        if result and result["time"] is not None:
            total_time += result["time"]
            if result["rank"] is not None:
                ranks.append(result["rank"])
        else:
            # Strafe: schlechteste Zeit + 50%
            worst_time = worst_time_per_track.get(track["name"], 120.0)
            total_time += worst_time * 1.5
            print(f"Strafe {player}, Zeit: {total_time}")

    avg_rank = sum(ranks) / len(ranks) if ranks else 9999
    output_data["players"].append({
        "name": player,
        "avgRank": round(avg_rank, 1),
        "totalTime": round(total_time, 3),
        "carColors": info.get("carColors", [])
    })

# 3️⃣ Sortieren nach totalTime
output_data["players"].sort(key=lambda p: p["totalTime"])
for i, player in enumerate(output_data["players"], 1):
    player["leaderboardRank"] = i

# --------------------
# Save leaderboard JSON
# --------------------
with open("leaderboard.json", "w") as f:
    json.dump(output_data, f, indent=2)
print("✅ leaderboard.json saved!")

# --------------------
# Update last track index
# --------------------
last_index = (last_index + TRACKS_PER_RUN) % len(TRACKS)
with open(LAST_TRACK_FILE, "w") as f:
    json.dump({"index": last_index}, f)
print(f"Next run will start at track index {last_index}")
