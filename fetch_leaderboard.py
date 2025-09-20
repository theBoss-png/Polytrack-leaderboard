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
REQUEST_RETRY_COUNT = 3
DELAY_BETWEEN_REQUESTS = 1.0
MAX_RANK = 20000  # how deep we check

# --------------------
# Community Tracks
# --------------------
COMMUNITY_TRACKS = [
    ("b7b253d6b0cc2ce8e6d5fe51cd3365bde09ad5de4e12256128e9b6493969085c", "Asguardia"),
    ("da1ef837b8412d32269e305d4031c47b59da08fca2b856d94890eaf58ec29b71", "Flying Dreams"),
    ("7537816191920c597d6a1f0ab03b50c4ae3d74b6e0f6eeb8ddb85653762c7a5d", "Ghost City"),
    ("fa1a61bb25e8a5a68f2b30fffe9ca3bdd448f4a5c249f8b2403b4f5323b6de45", "Mos Espa"),
    ("a054a6277181a7f0a46588f5cccd1b794f537e5efd09a173a9ca7e11d511f304", "Natsujo"),
    ("4d0f964b159d51d6906478bbb87e1edad21b0f1eb2972af947be34f2d8c49ae9", "90xRESET"),
    ("0544f97453f7b0e2a310dfb0dcd331b4060ae2e9cb14ac27dc5367183dab0513", "concrete jungle"),
    ("2ccd83e9419b6071ad9272b73e549e427b1a0f62d5305015839ae1e08fb86ce6", "lu muvimento"),
    ("f112ab979138b9916221cbf46329fa7377a745bdd18cd3d00b4ffd6a8a68f113", "Re: Akina"),
    ("b41ac84904b60d00efa5ab8bb60f42c929c16d8ebbfe2f77126891fcddab9c1c", "Hyperion's Sanctuary"),
    ("89f1a70d0e6be8297ec340a378b890f3fed7d0e20e3ef15b5d32ef4ef7ff1701", "Opal Palace"),
    ("2978b99f058cb3a2ce6f97c435c803b8d638400532d7c79028b2ec3d5e093882", "Snow Park"),
    ("2046c377ac7ec5326b263c46587f30b66ba856257ddc317a866e3e7f66a73929", "Winter Hollow"),
    ("b453c3afb4b5872213aee43249d6db38578e8e2ded4a96f840617c9c6e63a6b6", "Anubis"),
    ("23a46c3d4978a72be5f4a7fea236797aa31b52e577044ef4c6faa822ecc5cdc0", "Joenail Jones"),
    ("1aadcef252749318227d5cd4ce61a4a71526087857104fd57697b6fc63102e8a", "Arabica"),
    ("773eb0b02b97a72f3e482738cda7a5292294800497e16d9366e4f4c88a6f4e2d", "Clay Temples"),
    ("932da81567f2b223fa1a52d88d6db52016600c5b9df02218f06c9eb832ecddeb", "Desert Stallion"),
    ("97da746d9b3ddd5a861fa8da7fcb6f6402ffa21f8f5cf61029d7a947bad76290", "Las Calles"),
    ("19335bb082dfde2af4f7e73e812cd54cee0039a9eadf3793efee3ae3884ce423", "Last Remnant"),
    ("bc7d29657a0eb2d0abb3b3639edcf4ade61705132c7ca1b56719a7a110096afd", "Malformations"),
    ("faed71cf26ba4d183795ecc93e3d1b39e191e51d664272b512692b0f4f323ff5", "Sandline Ultimatum"),
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

# --------------------
# Fetch leaderboard entries for a single track
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
# Hash → Name mapping
# --------------------
hash_to_name = {}
for stored_name, user_info in user_ids.items():
    hashed_id = user_info.get("hash")
    hash_to_name[hashed_id] = stored_name

# --------------------
# Trackwise fetching
# --------------------
all_runs = []

for track_id, track_name in TRACKS:
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
        print(f"{actual_name:20} {rank:>6} {frames/1000:.3f}s")

    # Players without record
    for uid, stored_name in hash_to_name.items():
        if uid not in found_entries:
            all_runs.append(Run(stored_name, 0, track_name, None))
            print(f"{stored_name:20} {'No record':>6}")

# --------------------
# Build JSON for GitHub Pages
# --------------------
output_data = {"players": [], "tracks": []}

all_maps = sorted(set(r.map_name for r in all_runs))
all_players = list(user_ids.keys())

# Player stats
for player, info in user_ids.items():
    player_runs = [r for r in all_runs if r.name == player]
    total_time = 0.0
    ranks = []
    for track_id, track_name in TRACKS:
        run_for_map = next((r for r in player_runs if r.map_name == track_name), None)
        if run_for_map and run_for_map.rank is not None:
            total_time += run_for_map.frames / 1000.0
            ranks.append(run_for_map.rank)
        else:
            total_time += 120.0  # penalty
    avg_rank = sum(ranks) / len(ranks) if ranks else 9999
    output_data["players"].append({
        "name": player,
        "avgRank": round(avg_rank, 1),
        "totalTime": round(total_time, 3),
        "carColors": info.get("carColors", [])
    })

# Track stats
for track_id, track_name in TRACKS:
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
    output_data["tracks"].append({"name": track_name, "results": track_results})

# Save leaderboard JSON
with open("leaderboard.json", "w") as f:
    json.dump(output_data, f, indent=2)

print("✅ leaderboard.json saved!")
