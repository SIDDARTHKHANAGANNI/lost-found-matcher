# manual adjacency — locations close to each other on campus
# score: 1.0 = same location, 0.6 = nearby, 0.2 = far, 0.0 = unknown location
NEARBY_LOCATIONS = {
    "Library": {"Library": 1.0, "Block A": 0.6, "Canteen": 0.4, "Auditorium": 0.3},
    "Canteen": {"Canteen": 1.0, "Library": 0.4, "Block A": 0.5, "Sports Complex": 0.3},
    "Sports Complex": {"Sports Complex": 1.0, "Gym": 0.7, "Canteen": 0.3},
    "Gym": {"Gym": 1.0, "Sports Complex": 0.7},
    "Auditorium": {"Auditorium": 1.0, "Library": 0.3, "Block A": 0.5},
    "Block A": {"Block A": 1.0, "Library": 0.6, "Auditorium": 0.5, "Canteen": 0.5},
}

def location_score(loc1: str, loc2: str) -> float:
    return NEARBY_LOCATIONS.get(loc1, {}).get(loc2, 0.0)