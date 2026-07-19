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
    Score a single song against a user's taste profile.

    Scoring recipe (points are additive):
        +1.0  if the song's genre exactly matches the user's favorite genre
        +1.0  if the song's mood exactly matches the user's favorite mood
        up to +2.0 for energy similarity, computed as
              2.0 * (1.0 - abs(song_energy - target_energy)), which rewards
              closeness to the target rather than raw magnitude (0.0 when the
              energies are a full 1.0 apart)
        +0.5  if the user likes acoustic songs and the song's acousticness > 0.6

    NOTE: sensitivity-test weighting — genre is halved (2.0 -> 1.0) and energy
    is doubled (max 1.0 -> 2.0) relative to the original recipe.

    Parameters:
        user_prefs (Dict): The user's taste profile. Read with the rich keys
            favorite_genre / favorite_mood / target_energy / likes_acoustic,
            falling back to the starter keys genre / mood / energy so the CLI
            demo profile keeps working. Missing keys simply skip their rule.
        song (Dict): A single song row (as produced by load_songs), with
            genre, mood, energy, and acousticness among its keys.

    Returns:
        Tuple[float, List[str]]: A pair (total_score, reasons) where
            total_score is the unrounded sum of all points earned, and reasons
            is a list of short human-readable strings — one per rule that
            contributed a nonzero number of points, e.g.
            "genre match (+2.0)", "energy similarity (+0.73)". Rules that did
            not fire are omitted from the list.
    """
    # Read profile fields, tolerating the shorter starter keys and missing keys.
    fav_genre = user_prefs.get("favorite_genre", user_prefs.get("genre"))
    fav_mood = user_prefs.get("favorite_mood", user_prefs.get("mood"))
    target_energy = user_prefs.get("target_energy", user_prefs.get("energy"))
    likes_acoustic = user_prefs.get("likes_acoustic", False)

    score = 0.0
    reasons: List[str] = []

    # --- Genre: exact match (sensitivity test: halved from 2.0 to 1.0). ---
    if fav_genre is not None and song.get("genre") == fav_genre:
        score += 1.0
        reasons.append("genre match (+1.0)")

    # --- Mood: exact match. ---
    if fav_mood is not None and song.get("mood") == fav_mood:
        score += 1.0
        reasons.append("mood match (+1.0)")

    # --- Energy: reward closeness to the target, not high energy. ---
    if target_energy is not None:
        # 2.0 at an exact hit, decaying to 0.0 as the gap approaches 1.0
        # (sensitivity test: max contribution doubled from 1.0 to 2.0).
        similarity = 2.0 * (1.0 - abs(float(song.get("energy", 0.0)) - float(target_energy)))
        if similarity > 0:
            score += similarity  # keep the full-precision value in the score
            # Round only for the human-readable reason string.
            reasons.append(f"energy similarity (+{similarity:.2f})")

    # --- Acoustic: small bonus when the user wants acoustic and the song is. ---
    if likes_acoustic and float(song.get("acousticness", 0.0)) > 0.6:
        score += 0.5
        reasons.append("acoustic bonus (+0.5)")

    return score, reasons


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, List[str]]]:
    """
    Rank songs for a user and return the top k (the Ranking Rule).

    Scores every song with score_song (the Scoring Rule), pairs each song with
    its score and reasons, sorts by score from highest to lowest, and returns
    only the best k. The original song dicts are never mutated — each result is
    a new (song, score, reasons) tuple that references the same song dict.

    Parameters:
        user_prefs (Dict): The user's taste profile passed through to score_song.
        songs (List[Dict]): The catalog of song dicts to rank (e.g. from
            load_songs). This list is not modified.
        k (int): The maximum number of recommendations to return. Defaults to 5.
            If there are fewer than k songs, all of them are returned.

    Returns:
        List[Tuple[Dict, float, List[str]]]: Up to k tuples of
            (song, score, reasons), ordered by descending score.
    """
    # Pair each song with its (score, reasons); the * unpacks score_song's
    # (score, reasons) return so each item is a flat (song, score, reasons).
    scored = [(song, *score_song(user_prefs, song)) for song in songs]

    # sorted() returns a NEW list, so the caller's `songs` list is left in its
    # original order. Key on the score (index 1), highest first.
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
