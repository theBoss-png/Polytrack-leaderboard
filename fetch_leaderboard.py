import json
import requests
import time
from statistics import mean

VERSION = "0.5.1"
TRACKS = [
    ("9b7342b34b142912d70e8c24dd72e906e0afabd34f12045b41de567c77fda3c2", "108 (1)"),
    ("8a22b2036ba91629cd2138075bfb3a5046095d43d5bcca05d67281ef853a0107", "109 (2)"),
    ("961a63c49a875797f3d048a0d48b7f9e6bd8814e4f1a0fc410c45b05967542d0", "110 (3)"),
    ("aa3845591b4bb0d214e17580bbdcd81e135d9d4e1bcbc973f4a23238e684626a", "111 (4)"),
    ("daa3b3533b563affdab7f386f979de0567c5feb9c53f4ccbf31841b0af380d3a", "112 (5)"),
    ("563f6673f51f5d448618db3d70ce5d2d669240f30143029bcb018c1967a3d2f9", "113 (6)"),
]
DELAY_BETWEEN_REQUESTS = 0.5
LEADERBOARD_FILE = "leaderboard.json"
MAX_RANK_PER_TRACK = 50

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


def fetch_track(track_id, track_name):
    url = f"https://vps.kodub.com/leaderboard?version={VERSION}&trackId={track_id}&skip=0&amount={MAX_RANK_PER_TRACK}&onlyVerified=false"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        entries = r.json().get("entries", [])
    except Exception as e:
        print(f"❌ Error fetching {track_name}: {e}")
        return []

    results = []
    for i, entry in enumerate(entries[:MAX_RANK_PER_TRACK]):
        rank = i + 1
        user_id = entry.get("userId")
        name = entry.get("name", "Unknown")
        frames = entry.get("frames", 0)
        time_s = round(frames / 1000, 3)

        # Parse car colors correctly (hex to array)
        car_colors_hex = entry.get("carColors", "")
        car_colors = []
        if car_colors_hex and len(car_colors_hex) % 6 == 0:
            car_colors = [car_colors_hex[i:i+6] for i in range(0, len(car_colors_hex), 6)]

        points = POINTS_TABLE.get(rank, 0.0)

        results.append({
            "rank": rank,
            "player": name,
            "userId": user_id,
            "time": time_s,
            "points": points,
            "carColors": car_colors
        })

    return results


def build_leaderboard():
    all_tracks = []
    players = {}

    for track_id, track_name in TRACKS:
        print(f"\n🏁 Fetching {track_name} leaderboard...")
        results = fetch_track(track_id, track_name)
        all_tracks.append({"name": track_name, "results": results})

        for r in results:
            uid = r["userId"]
            if not uid:
                continue
            if uid not in players:
                players[uid] = {
                    "name": r["player"],
                    "userId": uid,
                    "carColors": r["carColors"],
                    "totalPoints": 0.0,
                    "ranks": []
                }
            players[uid]["totalPoints"] += r["points"]
            players[uid]["ranks"].append(r["rank"])

        time.sleep(DELAY_BETWEEN_REQUESTS)

    leaderboard_players = []
    for p in players.values():
        avg_rank = mean(p["ranks"]) if p["ranks"] else None
        leaderboard_players.append({
            "name": p["name"],
            "userId": p["userId"],
            "avgRank": round(avg_rank, 3) if avg_rank else None,
            "carColors": p["carColors"],
            "totalPoints": round(p["totalPoints"], 3)
        })

    leaderboard_players.sort(key=lambda x: x["totalPoints"], reverse=True)
    for i, p in enumerate(leaderboard_players, start=1):
        p["leaderboardRank"] = i

    data = {"tracks": all_tracks, "players": leaderboard_players}
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ leaderboard.json updated successfully ({len(leaderboard_players)} players total)")


if __name__ == "__main__":
    build_leaderboard()
