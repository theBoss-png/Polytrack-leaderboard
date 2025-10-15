import json
import requests
import time

# --------------------
# CONFIG
# --------------------
VERSION = "0.5.1"
TRACKS = [
    ("92bb4c33f5d1f8baf684dc214f0f321967c92dab87726ab0aba27cea9dbd8734", "1"),
    ("8103eafa75228d2db501bb2995deca1a9a4f29d45ee50c221dd5ccbcaefd7a72", "2"),
    ("3f7c652ae4a0804012a4415a515aef803b806ac750aad5c579a4fddd2aea6c52", "3"),
    ("8c8f09a092f13b46a4f60b1175c8b6f7eb56e72e55802463ff90d8b0c5a6223f", "4"),
    ("19d9532f837b4e639fb4474ba3c198d26e0fba23ed95bd7bb8b6c6db359ef4f3", "5"),
    ("8091591f45280c361e6a4fd126566e3b9a99e47c86776278554512c78b00bb0a", "6"),
    # Add more tracks as needed
]
DELAY_BETWEEN_REQUESTS = 0.5
LEADERBOARD_FILE = "leaderboard.json"
MAX_RANK_PER_TRACK = 50

# --------------------
# POINT SYSTEM
# --------------------
POINTS_TABLE = {
    1: 40000.0, 2: 20000.0, 3: 13333.333333, 4: 10000.0, 5: 8000.0,
    6: 6666.666667, 7: 5714.285714, 8: 5000.0, 9: 4444.444444, 10: 4000.0,
    11: 3618.181818, 12: 3466.666667, 13: 3338.461538, 14: 3228.571429, 15: 3133.333333,
    16: 3050.0, 17: 2976.470588, 18: 2911.111111, 19: 2852.631579, 20: 2800.0,
    21: 2752.380952, 22: 2709.090909, 23: 2669.565217, 24: 2633.333333, 25: 2600.0,
    26: 2569.230769, 27: 2540.740741, 28: 2514.285714, 29: 2489.655172, 30: 2466.666667,
    31: 2445.16129, 32: 2425.0, 33: 2406.060606, 34: 2388.235294, 35: 2371.428571,
    36: 2355.555556, 37: 2340.540541, 38: 2326.315789, 39: 2312.820513, 40: 2300.0,
    41: 2287.804878, 42: 2276.190476, 43: 2265.116279, 44: 2254.545455, 45: 2244.444444,
    46: 2234.782609, 47: 2225.531915, 48: 2216.666667, 49: 2208.163265, 50: 2200.0
}


# --------------------
# Fetch leaderboard for one track
# --------------------
def fetch_track(track_id, track_name, max_rank=MAX_RANK_PER_TRACK):
    url = f"https://vps.kodub.com/leaderboard?version={VERSION}&trackId={track_id}&skip=0&amount={max_rank}&onlyVerified=false"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        entries = r.json().get("entries", [])
    except Exception as e:
        print(f"❌ Error fetching {track_name}: {e}")
        return []

    results = []
    for i, entry in enumerate(entries[:max_rank]):
        rank = i + 1
        name = entry.get("name", "Unknown")
        frames = entry.get("frames", 0)
        time_s = round(frames / 1000, 3)
        points = POINTS_TABLE.get(rank, 0.0)

        results.append({
            "rank": rank,
            "player": name,
            "time": time_s,
            "points": points
        })

    return results


# --------------------
# Build complete leaderboard
# --------------------
def build_leaderboard():
    all_tracks = []
    player_points = {}

    for track_id, track_name in TRACKS:
        print(f"\n🏁 Fetching {track_name} leaderboard...")
        results = fetch_track(track_id, track_name)

        # Track-specific leaderboard (top 50 only)
        all_tracks.append({
            "name": track_name,
            "results": results
        })

        # Update player total points (keep everyone)
        for res in results:
            player_points[res["player"]] = player_points.get(res["player"], 0.0) + res["points"]

        time.sleep(DELAY_BETWEEN_REQUESTS)

    # Create overall leaderboard (every player who appeared)
    players = [
        {"name": name, "totalPoints": round(points, 3)}
        for name, points in player_points.items()
    ]
    players.sort(key=lambda x: x["totalPoints"], reverse=True)

    # Add rank number
    for i, player in enumerate(players, 1):
        player["rank"] = i

    # Write JSON file
    output = {"tracks": all_tracks, "players": players}
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ leaderboard.json updated successfully ({len(players)} players total)")


# --------------------
# Run script
# --------------------
if __name__ == "__main__":
    build_leaderboard()
