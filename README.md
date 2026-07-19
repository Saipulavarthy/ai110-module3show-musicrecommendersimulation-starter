# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This is VibeFinder 1.0, a content-based music recommender simulation. It scores an 18-song catalog against a single user's stated taste profile (favorite genre, favorite mood, target energy, and acoustic preference) using a transparent weighted scoring formula, then returns a ranked top-k list with plain-language explanations for each recommendation.

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

Real recommenders like Spotify and YouTube predict what you'll enjoy next in two main ways. Collaborative filtering learns from other users ("people who liked what you liked also liked this"), while content-based filtering looks at the song's own attributes — tempo, energy, mood — and finds similar songs. At scale they blend both, feeding on likes, skips, play counts, audio features, and context through deep-learning models tuned to keep you listening.

My simulation is a simple content-based recommender. It ignores other users and scores each song by how well its attributes match one user's taste. The key idea is that it rewards closeness, not magnitude — a song is better when its energy sits near the user's target, not just when it's high. Genre carries the most weight, then energy closeness, then mood, then a small acoustic bonus.

Each Song uses genre and mood (categorical matches), energy and acousticness (numeric); tempo_bpm, valence, and danceability are available for later, and id/title/artist are just for display. The UserProfile stores favorite_genre, favorite_mood, target_energy, and likes_acoustic.

Two rules produce a recommendation: the Scoring Rule (score_song) scores one song from those weighted features, and the Ranking Rule (recommend_songs) scores every song, sorts them, and returns the top k.

This system likely over-prioritizes genre matches, since a 2.0-point genre bonus can outweigh strong mood and energy alignment combined. A song that's a near-perfect mood and energy match but in a different genre could rank below a mediocre song that merely shares the favorite genre. This risks creating a "filter bubble" — the recommender may keep surfacing the same genre repeatedly rather than surfacing genuinely well-matched songs across genres, and it has no way to detect if a user's taste is evolving or situational (e.g. wanting something energetic on some days, chill on others) since target_energy is a single fixed value rather than a range.p

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```
========================================================================== test session starts ==========================================================================
platform darwin -- Python 3.11.7, pytest-7.4.0, pluggy-1.0.0 -- /opt/anaconda3/bin/python
cachedir: .pytest_cache
rootdir: /Users/harithaadhikarla/Desktop/CodePath/ai110-module3show-musicrecommendersimulation-starter
plugins: anyio-4.14.2, dash-3.2.0
collected 8 items                                                                                                                                                       

tests/test_recommender.py::test_recommend_returns_songs_sorted_by_score PASSED                                                                                    [ 12%]
tests/test_recommender.py::test_explain_recommendation_returns_non_empty_string PASSED                                                                            [ 25%]
tests/test_recommender.py::test_genre_match_outranks_perfect_mood_energy_without_acoustic PASSED                                                                  [ 37%]
tests/test_recommender.py::test_absent_genre_returns_results_but_none_reach_genre_score PASSED                                                                    [ 50%]
tests/test_recommender.py::test_contradictory_profile_demotes_perfect_categorical_match PASSED                                                                    [ 62%]
tests/test_recommender.py::test_acoustic_bonus_never_applies_to_non_acoustic_favorite PASSED                                                                      [ 75%]
tests/test_recommender.py::test_acoustic_threshold_is_a_hard_cliff_at_0_6 PASSED                                                                                  [ 87%]
tests/test_recommender.py::test_energy_similarity_only_ever_adds_never_penalizes PASSED                                                                           [100%]

=========================================================================== 8 passed in 0.02s ===========================================================


You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

Recommendations for profile: pop / happy

1. Sunrise City — Neon Echo
   Score: 3.98
   Reasons: genre match (+2.0), mood match (+1.0), energy similarity (+0.98)

2. Gym Hero — Max Pulse
   Score: 2.87
   Reasons: genre match (+2.0), energy similarity (+0.87)

3. Rooftop Lights — Indigo Parade
   Score: 1.96
   Reasons: mood match (+1.0), energy similarity (+0.96)

4. Night Drive Loop — Neon Echo
   Score: 0.95
   Reasons: energy similarity (+0.95)

5. Concrete Kings — MC Verdict
   Score: 0.94
   Reasons: energy similarity (+0.94)

```
# e.g.:
# User profile: genre=indie, mood=chill, energy=low
# Recommendations:
#   1. ...
#   2. ...
#   3. ...


```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

I halved the genre weight and doubled the max energy weight to test how sensitive the rankings are to my original weighting choices.

**Result:** Sunrise City stayed #1 in both versions, since it wins on genre, mood, and energy regardless of weighting. But Rooftop Lights and Gym Hero swapped places — Rooftop Lights (no genre match, but a mood match and near-perfect energy) overtook Gym Hero (a genre match with no mood match) once energy carried double weight.

**Was it more accurate, or just different?** I'd call this "different" rather than clearly "more accurate" — it's a value judgment, not a correctness issue. Rooftop Lights is indie pop, a close cousin to pop, so arguably deserves to rank near the top of a "pop / happy" profile; the new weighting captures that. But this also means genre no longer guarantees a floor over mood+energy combinations, which could make a pure "I want rock" request return more non-rock songs than expected.

Also tested four adversarial profiles (see `model_card.md` Evaluation section for full details): an internally contradictory profile, a genre-absent profile, a genre-vs-mood tie, and an acoustic dead-weight profile — each exposed a different structural limitation in the scoring logic.

---
## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

- The catalog only has 18 songs, so several genres appear only once or twice — far too small to represent real musical diversity.
- Genre is treated as a strict match, not a spectrum, so closely related genres (e.g. indie pop vs. pop) score identically to completely unrelated ones.
- The system has no way to detect internally contradictory profiles (e.g. wanting "chill" mood at high energy) — it silently returns a mediocre score instead of flagging the conflict.
- There's no fallback when a user's favorite genre doesn't exist in the catalog — it always returns a full top-5 list, even when nothing meaningfully matches.
- It doesn't understand lyrics, language, or anything beyond the six numeric/categorical features in the CSV.


---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this

