from datetime import datetime, timedelta
from app.services.location import location_score
from app.services.matching import time_score

def test_location_score_same_location():
    assert location_score("Library", "Library") == 1.0

def test_location_score_nearby():
    assert location_score("Library", "Canteen") == 0.4

def test_location_score_unknown_pair():
    assert location_score("Library", "Random Place") == 0.0

def test_time_score_same_moment():
    now = datetime.utcnow()
    assert time_score(now, now) == 1.0

def test_time_score_decays_with_gap():
    t1 = datetime.utcnow()
    t2 = t1 + timedelta(days=7)
    score = time_score(t1, t2)
    assert 0.4 < score < 0.6  # halfway through 14-day window

def test_time_score_zero_beyond_max_days():
    t1 = datetime.utcnow()
    t2 = t1 + timedelta(days=20)
    assert time_score(t1, t2) == 0.0