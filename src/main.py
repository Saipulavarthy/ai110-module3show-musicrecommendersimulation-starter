"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path

# Works both as `python -m src.main` (from the repo root) and as
# `python main.py` (from inside src/).
try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs

# Anchor the data path to this file, so the app finds songs.csv no matter
# what the current working directory is.
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


def main() -> None:
    songs = load_songs(str(DATA_PATH))

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    # Header: show which profile these recommendations were built for.
    genre = user_prefs.get("favorite_genre", user_prefs.get("genre", "any"))
    mood = user_prefs.get("favorite_mood", user_prefs.get("mood", "any"))
    print(f"\nRecommendations for profile: {genre} / {mood}\n")

    # Ranked list: "1. Title — Artist", then indented Score and Reasons lines.
    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        title = song.get("title", "Unknown title")
        artist = song.get("artist")
        header = f"{rank}. {title} — {artist}" if artist else f"{rank}. {title}"
        print(header)
        print(f"   Score: {score:.2f}")
        reasons_text = ", ".join(reasons) if reasons else "no strong matches"
        print(f"   Reasons: {reasons_text}")
        print()


if __name__ == "__main__":
    main()
