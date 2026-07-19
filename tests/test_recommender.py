from pathlib import Path

import pytest

from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    load_songs,
    score_song,
    recommend_songs,
)

# Real catalog, anchored to the repo so tests run from any working directory.
CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "songs.csv"


@pytest.fixture
def catalog():
    return load_songs(str(CATALOG_PATH))

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- Adversarial / edge-case regression tests -------------------------------
# These lock in behaviors we found by stress-testing the point-based Scoring
# Rule (genre +2.0, mood +1.0, energy up to +1.0, acoustic +0.5) against the
# real catalog. They document deliberate properties AND known sharp edges, so a
# future change to the weights will trip a test instead of silently shifting
# the recommendations.


def _title_of(result):
    """Pull the song title out of a (song, score, reasons) result tuple."""
    return result[0]["title"]


def test_genre_match_outranks_perfect_mood_energy_without_acoustic(catalog):
    """
    A genre match has a hard floor of 2.0 (2.0 + any energy >= 2.0), while a
    mood match plus perfect energy has a ceiling of 2.0 (1.0 + 1.0). So a genre
    match must never be beaten by a pure mood+energy match when no acoustic
    bonus is in play. metal/sad@0.20 is the tightest case in the catalog:
    Iron Verdict (genre match, terrible energy) still edges out Fading Light
    (perfect mood + perfect energy).
    """
    prefs = {
        "favorite_genre": "metal",
        "favorite_mood": "sad",
        "target_energy": 0.20,
        "likes_acoustic": False,
    }
    results = recommend_songs(prefs, catalog, k=len(catalog))

    iron = next(r for r in results if _title_of(r) == "Iron Verdict")
    fading = next(r for r in results if _title_of(r) == "Fading Light")

    assert iron[1] == pytest.approx(2.24)   # 2.0 genre + 0.24 energy
    assert fading[1] == pytest.approx(2.00)  # 1.0 mood + 1.0 energy
    assert iron[1] > fading[1]
    assert _title_of(results[0]) == "Iron Verdict"


def test_absent_genre_returns_results_but_none_reach_genre_score(catalog):
    """
    When the favorite genre is absent from the catalog, the dominant +2.0
    signal can never fire, so the ranking collapses onto energy/mood and NO
    result can reach the 2.0 a genre match would guarantee. The recommender
    still fills the top-k (no empty-result signal) — that is the weakness this
    documents.
    """
    prefs = {
        "favorite_genre": "reggae",   # not present anywhere in the catalog
        "favorite_mood": "euphoric",
        "target_energy": 0.5,
        "likes_acoustic": False,
    }
    results = recommend_songs(prefs, catalog, k=5)

    assert len(results) == 5                       # still returns a full list
    assert all(score < 2.0 for _, score, _ in results)  # none is a genre match
    # No result may claim a genre match in its reasons.
    assert all(
        not any("genre match" in reason for reason in reasons)
        for _, _, reasons in results
    )


def test_contradictory_profile_demotes_perfect_categorical_match(catalog):
    """
    lofi/chill is inherently low-energy, so pairing it with target_energy=0.95
    is internally contradictory. The best categorical match still ranks #1, but
    its score is silently dragged below 3.5 by the energy penalty even though
    genre + mood alone are worth 3.0. The system serves the contradiction
    without flagging it.
    """
    prefs = {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.95,
        "likes_acoustic": False,
    }
    results = recommend_songs(prefs, catalog, k=5)
    top_song, top_score, top_reasons = results[0]

    assert top_song["genre"] == "lofi" and top_song["mood"] == "chill"
    assert "genre match (+2.0)" in top_reasons
    assert "mood match (+1.0)" in top_reasons
    # 3.0 of categorical match, but energy drags it into the low-3s, not ~4.
    assert 3.0 < top_score < 3.5


def test_acoustic_bonus_never_applies_to_non_acoustic_favorite(catalog):
    """
    EDM is structurally non-acoustic, so likes_acoustic=True is dead weight for
    an EDM lover: their perfect match earns NO acoustic bonus, while the bonus
    instead lands on genre-irrelevant acoustic songs elsewhere in the list.
    """
    prefs = {
        "favorite_genre": "edm",
        "favorite_mood": "euphoric",
        "target_energy": 0.90,
        "likes_acoustic": True,
    }
    results = recommend_songs(prefs, catalog, k=5)
    top_song, top_score, top_reasons = results[0]

    assert top_song["title"] == "Neon Horizon"
    assert top_score == pytest.approx(4.0)  # 2.0 + 1.0 + 1.0, NO acoustic bonus
    assert not any("acoustic bonus" in r for r in top_reasons)
    # ...yet the bonus does fire, on genre-irrelevant songs further down.
    assert any(
        song["genre"] != "edm" and any("acoustic bonus" in r for r in reasons)
        for song, _, reasons in results
    )


def test_acoustic_threshold_is_a_hard_cliff_at_0_6():
    """
    The acoustic bonus uses a strict acousticness > 0.6 cutoff, so two
    otherwise-identical songs straddling 0.60 get a full 0.5-point swing. This
    documents the discontinuity (a continuous 0.5*acousticness term would avoid
    it).
    """
    prefs = {
        "favorite_genre": "none",
        "favorite_mood": "none",
        "target_energy": 0.5,
        "likes_acoustic": True,
    }
    base = {"genre": "x", "mood": "y", "energy": 0.5}
    at_threshold = {**base, "acousticness": 0.60}   # 0.60 is NOT > 0.60
    just_above = {**base, "acousticness": 0.61}

    score_at, reasons_at = score_song(prefs, at_threshold)
    score_above, reasons_above = score_song(prefs, just_above)

    assert score_above - score_at == pytest.approx(0.5)
    assert not any("acoustic bonus" in r for r in reasons_at)
    assert any("acoustic bonus" in r for r in reasons_above)


def test_energy_similarity_only_ever_adds_never_penalizes():
    """
    Energy closeness is 1.0 - abs(diff), floored at 0 and then omitted from
    reasons when it contributes nothing. A maximally-distant energy must add
    exactly 0 (not a negative penalty) and produce no energy reason.
    """
    prefs = {
        "favorite_genre": "none",
        "favorite_mood": "none",
        "target_energy": 0.0,
        "likes_acoustic": False,
    }
    far_song = {"genre": "x", "mood": "y", "energy": 1.0, "acousticness": 0.0}

    score, reasons = score_song(prefs, far_song)

    assert score == pytest.approx(0.0)
    assert reasons == []
