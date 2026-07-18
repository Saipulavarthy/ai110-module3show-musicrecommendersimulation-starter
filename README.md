# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

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

This system likely over-prioritizes genre matches, since a 2.0-point genre bonus can outweigh strong mood and energy alignment combined. A song that's a near-perfect mood and energy match but in a different genre could rank below a mediocre song that merely shares the favorite genre. This risks creating a "filter bubble" — the recommender may keep surfacing the same genre repeatedly rather than surfacing genuinely well-matched songs across genres, and it has no way to detect if a user's taste is evolving or situational (e.g. wanting something energetic on some days, chill on others) since target_energy is a single fixed value rather than a range.

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

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Paste a sample of your recommender's output here as a text block so a reader can see what it produces:

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

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



