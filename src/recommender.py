import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# --- Algorithm Recipe: weights for the scoring rule -------------------------
# Genre is the strongest, most independent signal, so it carries the most
# weight. Energy closeness is the backbone of "vibe". Mood partly overlaps with
# energy, so it is worth less. Acoustic preference is a small tie-breaker.
GENRE_WEIGHT = 0.40
ENERGY_WEIGHT = 0.30
MOOD_WEIGHT = 0.20
ACOUSTIC_WEIGHT = 0.10

# How far a song's energy can drift from the target before it scores 0.
DEFAULT_ENERGY_TOLERANCE = 0.25
# Partial credit given to a genre that is "acceptable" but not the favorite.
ACCEPTABLE_GENRE_CREDIT = 0.5

# Numeric columns in data/songs.csv that must be parsed as floats.
_NUMERIC_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    The first four fields are the core profile. The optional fields make the
    profile fairer without turning it into an ML system:
      - acceptable_genres: genres that earn partial genre credit, so a chill
        ambient track isn't punished just for not being the favorite genre.
      - energy_tolerance: how picky the user is about energy. Smaller = stricter.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    acceptable_genres: List[str] = field(default_factory=list)
    energy_tolerance: float = DEFAULT_ENERGY_TOLERANCE


def _score_core(
    fav_genre: Optional[str],
    acceptable_genres: List[str],
    fav_mood: Optional[str],
    target_energy: Optional[float],
    energy_tolerance: Optional[float],
    likes_acoustic: bool,
    song_genre: str,
    song_mood: str,
    song_energy: float,
    song_acousticness: float,
) -> Tuple[float, List[str]]:
    """
    Shared Scoring Rule used by both the OOP and functional entry points.
    Returns (score, reasons) for a single song.
    """
    score = 0.0
    reasons: List[str] = []

    # --- Genre: full credit for the favorite, partial for an acceptable one ---
    if fav_genre and song_genre == fav_genre:
        score += GENRE_WEIGHT
        reasons.append(f"matches your favorite genre ({song_genre})")
    elif acceptable_genres and song_genre in acceptable_genres:
        score += GENRE_WEIGHT * ACCEPTABLE_GENRE_CREDIT
        reasons.append(f"is a genre you also enjoy ({song_genre})")

    # --- Mood: exact match bonus ---
    if fav_mood and song_mood == fav_mood:
        score += MOOD_WEIGHT
        reasons.append(f"matches your mood ({song_mood})")

    # --- Energy: reward closeness to the target, not high values ---
    if target_energy is not None:
        tol = energy_tolerance if energy_tolerance and energy_tolerance > 0 else DEFAULT_ENERGY_TOLERANCE
        closeness = max(0.0, 1.0 - abs(song_energy - target_energy) / tol)
        score += ENERGY_WEIGHT * closeness
        if closeness >= 0.6:
            reasons.append(f"energy ({song_energy:.2f}) is close to your target ({target_energy:.2f})")

    # --- Acoustic: continuous bonus when the user likes acoustic songs ---
    if likes_acoustic:
        score += ACOUSTIC_WEIGHT * song_acousticness
        if song_acousticness >= 0.6:
            reasons.append("has the acoustic sound you like")

    return score, reasons


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        return _score_core(
            fav_genre=user.favorite_genre,
            acceptable_genres=user.acceptable_genres,
            fav_mood=user.favorite_mood,
            target_energy=user.target_energy,
            energy_tolerance=user.energy_tolerance,
            likes_acoustic=user.likes_acoustic,
            song_genre=song.genre,
            song_mood=song.mood,
            song_energy=song.energy,
            song_acousticness=song.acousticness,
        )

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # Scoring Rule for every song, then the Ranking Rule: sort + take top k.
        scored = [(song, self._score(user, song)[0]) for song in self.songs]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = self._score(user, song)
        if not reasons:
            return "Included as a fallback — it didn't strongly match your profile."
        return "Recommended because it " + ", and ".join(reasons) + "."


def load_songs(filepath: str) -> List[Dict]:
    """
    Load songs from a CSV file into a list of dictionaries.

    csv.DictReader reads every column as a string, so the numeric feature
    columns are converted to float and the id column to int; the remaining
    text columns (title, artist, genre, mood) are left as strings.

    Parameters:
        filepath (str): Path to the CSV file to read. The file is expected to
            have a header row matching the columns in data/songs.csv.

    Returns:
        List[Dict]: One dictionary per song row, keyed by column name, with
            energy, tempo_bpm, valence, danceability, and acousticness as
            floats and id as an int.
    """
    songs: List[Dict] = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in _NUMERIC_FIELDS:
                if key in row and row[key] != "":
                    row[key] = float(row[key])
            if "id" in row and row["id"] != "":
                row["id"] = int(row["id"])
            songs.append(row)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song (dict) against user preferences (dict).
    Accepts either the rich keys (favorite_genre/favorite_mood/target_energy)
    or the short starter keys (genre/mood/energy).
    Required by recommend_songs() and src/main.py
    """
    fav_genre = user_prefs.get("favorite_genre", user_prefs.get("genre"))
    fav_mood = user_prefs.get("favorite_mood", user_prefs.get("mood"))
    target_energy = user_prefs.get("target_energy", user_prefs.get("energy"))

    return _score_core(
        fav_genre=fav_genre,
        acceptable_genres=user_prefs.get("acceptable_genres", []),
        fav_mood=fav_mood,
        target_energy=target_energy,
        energy_tolerance=user_prefs.get("energy_tolerance"),
        likes_acoustic=user_prefs.get("likes_acoustic", False),
        song_genre=song.get("genre", ""),
        song_mood=song.get("mood", ""),
        song_energy=float(song.get("energy", 0.0)),
        song_acousticness=float(song.get("acousticness", 0.0)),
    )


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song (Scoring Rule) then sorts and takes the top k (Ranking Rule).
    Returns (song_dict, score, explanation).
    Required by src/main.py
    """
    scored: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        if reasons:
            explanation = "it " + ", and ".join(reasons)
        else:
            explanation = "it was included as a fallback"
        scored.append((song, score, explanation))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]
