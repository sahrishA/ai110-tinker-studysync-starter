"""
StudySync -- Find a Study Spot (Ticket 3, Tinker 3B).

TICKET: implemented loading, scoring, ranking, and formatting functions.
"""

import csv

NOISE_ORDER = {"quiet": 0, "moderate": 1, "loud": 2}


def load_study_spots(csv_path: str) -> list:
    """
    Load study spots from a CSV into a list of dicts, converting
    "distance_miles" to float and "seats_available" to int.
    """
    spots = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Convert numeric fields
            row["distance_miles"] = float(row["distance_miles"]) if row.get("distance_miles") not in (None, "") else 0.0
            row["seats_available"] = int(row["seats_available"]) if row.get("seats_available") not in (None, "") else 0
            spots.append(row)
    return spots


def score_study_spot(profile: dict, spot: dict) -> tuple:
    """
    Score one study spot against a student profile.

    profile example: {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}

    Return (score, reasons) where reasons is a list of short strings
    explaining what contributed to the score, e.g. ["quiet enough", "close enough"].
    """
    reasons = []

    # Weights (tuneable)
    noise_weight = 5.0
    distance_weight = 3.0
    seats_weight = 2.0

    score = 0.0

    # Noise: lower is better. Use NOISE_ORDER to compare.
    spot_noise = spot.get("noise_level")
    profile_max_noise = profile.get("max_noise")
    if spot_noise is None or profile_max_noise is None:
        reasons.append("noise info missing")
    else:
        spot_order = NOISE_ORDER.get(spot_noise, 999)
        max_order = NOISE_ORDER.get(profile_max_noise, 999)
        if spot_order <= max_order:
            score += noise_weight
            reasons.append(f"noise OK ({spot_noise})")
        else:
            score -= noise_weight
            reasons.append(f"too noisy ({spot_noise})")

    # Distance: closer is better. If within max_distance, award points proportional
    # to how much closer it is. If beyond, apply a penalty.
    spot_distance = spot.get("distance_miles", 0.0)
    max_distance = profile.get("max_distance")
    if max_distance is None:
        reasons.append("distance preference missing")
    else:
        try:
            d = float(spot_distance)
            if d <= max_distance:
                # The closer, the more points (0..distance_weight)
                if max_distance == 0:
                    # avoid division by zero, treat exact match as full points
                    dist_score = distance_weight
                else:
                    dist_score = distance_weight * (1 - (d / max_distance))
                score += dist_score
                reasons.append(f"close enough ({d} mi)")
            else:
                score -= distance_weight
                reasons.append(f"too far ({d} mi)")
        except (TypeError, ValueError):
            reasons.append("distance data invalid")

    # Seats: more seats is better. If at least min_seats, award up to seats_weight
    # proportionally (cap at seats_weight). If not enough, apply a penalty.
    spot_seats = spot.get("seats_available", 0)
    min_seats = profile.get("min_seats")
    if min_seats is None:
        reasons.append("seat preference missing")
    else:
        try:
            s = int(spot_seats)
            if s >= min_seats and min_seats > 0:
                seat_score = seats_weight * min(1.0, s / min_seats)
                score += seat_score
                reasons.append(f"enough seats ({s})")
            else:
                score -= seats_weight
                reasons.append(f"not enough seats ({s})")
        except (TypeError, ValueError):
            reasons.append("seat data invalid")

    return score, reasons


def rank_study_spots(profile: dict, spots: list, k: int = 3) -> list:
    """
    Score every study spot, then return the top k as (spot, score, reasons)
    tuples, sorted by score descending.
    """
    scored = []
    for spot in spots:
        s, reasons = score_study_spot(profile, spot)
        scored.append((spot, s, reasons))

    ranked = sorted(scored, key=lambda t: t[1], reverse=True)[:k]
    return ranked


def format_results(ranked: list) -> None:
    """Print each ranked study spot with its score and reasons, one line each."""
    for i, (spot, score, reasons) in enumerate(ranked, start=1):
        name = spot.get("name", "<unknown>")
        reason_text = ", ".join(reasons) if reasons else "no reasons"
        print(f"{i}. {name} -- Score: {score:.1f} -- Because: {reason_text}")


def render_study_spot_tab():
    import streamlit as st

    st.subheader("Find a Study Spot")
    max_noise = st.selectbox("Max noise level", ["quiet", "moderate", "loud"], index=1)
    max_distance = st.slider("Max distance (miles)", 0.0, 3.0, 1.0)
    min_seats = st.number_input("Minimum seats needed", min_value=1, value=4, step=1)

    if st.button("Find spots"):
        profile = {"max_noise": max_noise, "max_distance": max_distance, "min_seats": min_seats}
        try:
            spots = load_study_spots("data/study_spots.csv")
            ranked = rank_study_spots(profile, spots, k=3)
            for spot, score, reasons in ranked:
                st.write(f"**{spot['name']}** -- Score: {score:.1f} -- Because: {', '.join(reasons)}")
        except NotImplementedError:
            st.warning("🚧 Ranking isn't implemented yet -- that's Tinker 3B's ticket.")


if __name__ == "__main__":
    spots = load_study_spots("data/study_spots.csv")
    profile = {"max_noise": "moderate", "max_distance": 1.0, "min_seats": 4}
    ranked = rank_study_spots(profile, spots, k=3)
    format_results(ranked)
