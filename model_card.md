# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

VibeFinder 

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

This is a classroom simulation, not a real production recommender. It's designed to demonstrate how a simple content-based system converts a user's stated taste (genre, mood, energy, and acoustic preference) into a ranked list of song suggestions using transparent, hand-written rules — not machine learning. It assumes the user can articulate their taste as a single genre/mood/energy target, which is a simplification real listeners rarely fit into. It's meant for exploring how recommendation logic works and where it breaks, not for actually recommending music to real users at scale.
---

## 3. How the Model Works  

Explain your scoring approach in simple language.  

Prompts:  

- What features of each song are used (genre, energy, mood, etc.)  
- What user preferences are considered  
- How does the model turn those into a score  
- What changes did you make from the starter logic  

Avoid code here. Pretend you are explaining the idea to a friend who does not program.

Every song is scored against the user's stated taste using a few simple rules: songs get extra points for sharing the user's favorite genre, more points for sharing the user's favorite mood, and a partial score based on how close the song's energy is to what the user wants (closer energy = more points, regardless of whether it's above or below the target). Songs also get a small bonus if the user likes acoustic music and the song is acoustic enough. Once every song in the catalog has a score, they're sorted from highest to lowest, and the top handful are returned as recommendations, along with a plain-language list of reasons explaining why each song scored the way it did.
---

## 4. Data  

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

The catalog has 18 songs, expanded from a 10-song starter file. It spans 15 genres (pop, lofi, rock, ambient, jazz, synthwave, indie pop, classical, hip-hop, metal, r&b, folk, edm, blues, country) and a wide range of moods (happy, chill, intense, relaxed, moody, focused, sad, confident, angry, romantic, nostalgic, euphoric, melancholic, uplifting). Each song has genre, mood, energy, tempo_bpm, valence, danceability, and acousticness. Several genres appear only once or twice, so the catalog is far too small and unevenly distributed to represent real musical diversity — it's meant to illustrate the recommender's logic, not to reflect an actual music library.
---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

The system works well for users whose stated genre actually exists clearly in the catalog and whose energy target is coherent with their mood (e.g. a "pop / happy / high energy" profile reliably surfaces upbeat pop songs first). The energy-similarity rule captures a genuinely useful idea — rewarding closeness rather than raw magnitude — so it correctly distinguishes a "medium energy" listener from both extremes rather than just favoring the highest-energy songs. The reasons list also does its job well: for any recommendation, a user can see exactly why a song was suggested, which makes the system easy to audit and explain, unlike a black-box ML model.
---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

This system has a hard genre floor: any exact genre match scores at least 2.0 points, while the best possible mood+energy combination (without a genre match) caps out at exactly 2.0. This means a song that's a perfect mood and energy match, but doesn't share the user's favorite genre, can never outrank an otherwise poor genre match — creating a structural bias toward genre loyalty over overall "vibe" similarity. Combined with an 18-song catalog where several genres appear only once or twice, this risks a filter bubble: users get pushed toward repeatedly hearing their stated favorite genre rather than genuinely well-matched songs from adjacent genres (e.g. indie pop for a pop fan). The system also has no way to detect or flag internally contradictory profiles (e.g. wanting "chill" mood at high target_energy), silently returning a mediocre score instead of surfacing the conflict, and it has no fallback behavior when a user's favorite genre doesn't exist in the catalog at all — it always returns a full top-5 list, even when nothing meaningfully matches.
That's about 5 sentences and pulls directly from your Profile A, B, and C findings — real,
---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

I tested the recommender against seven user profiles: a baseline "pop / happy" profile, three additional baseline profiles (high-energy pop, chill lofi, deep intense rock), and four adversarial profiles designed to stress-test the scoring logic (an internally contradictory profile, a genre-absent profile, a genre-vs-mood tie, and an acoustic dead-weight profile).

**What surprised me:** The most surprising result was that the system has no real notion of "genre similarity" — it treats genre as a strict yes/no match, not a spectrum. Rooftop Lights (indie pop) and Sunrise City (pop) sound like close cousins to a human listener, but the system treats "indie pop" as a complete genre mismatch, worth zero points, just as much as if the song were death metal. It took a hard genre-vs-mood tie test (Profile C) to notice that this isn't a minor quirk — it's a structural property: a genre match has a mathematical floor of 2.0 points, while mood + energy together can only ever tie that floor, never beat it.

**Profile comparisons:**

- **Pop/happy vs. chill lofi:** The pop/happy profile favors upbeat, high-energy tracks like Sunrise City and Gym Hero, while the chill lofi profile favors low-energy, mellow tracks like Midnight Coding and Library Rain. This makes sense — the two profiles target opposite ends of the energy scale, so their top results barely overlap.

- **Pop/happy vs. deep intense rock:** The rock profile pulls entirely different songs to the top (Storm Runner, Iron Verdict) because genre match dominates the score, and none of the pop-favoring songs share the "rock" genre tag. This confirms the genre weight is doing exactly what it's designed to do — strongly separate users by stated genre preference.

- **Genre-vs-mood tie (Profile C) vs. pop/happy:** Where pop/happy has a genre it can actually satisfy, Profile C (metal/sad/low-energy) exposes what happens when the genre match and the user's actual energy/mood preference pull in opposite directions. Iron Verdict (metal, high-energy) wins on genre alone, barely edging out Fading Light (classical, genuinely sad and low-energy). In plain language: it's a bit like recommending a heavy metal song to someone who says they want something sad and quiet, purely because they said they liked metal — the system takes the genre label at face value and doesn't notice that a specific song doesn't actually fit the vibe the same person is asking for.

- **Acoustic dead-weight (Profile D) vs. pop/happy:** In the pop/happy profile, the acoustic bonus never comes up because it's not part of that profile's preferences. In Profile D (EDM lover who also says they like acoustic songs), the bonus actively works against the user's real taste — it nudges unrelated lofi tracks upward for being acoustic, even though the user's favorite genre (EDM) can never be acoustic. This is the clearest case of a "well-intentioned" feature doing the wrong job: the acoustic bonus was meant to add nuance, but for certain genre lovers it just adds noise.

**Why "Gym Hero" keeps showing up for "Happy Pop" fans:** Imagine you tell a friend "I want something happy and poppy." Gym Hero is a pop song, so it checks the "genre" box right away — worth the most points in this system. Even though it's not tagged "happy" (it's tagged "intense"), it's still energetic and upbeat enough on the energy scale to rack up a lot of points there too. So even though it's not a perfect match to "happy," it satisfies enough of what the system is measuring (genre + high energy) to consistently land near the top — the system just doesn't have a way to tell the difference between "happy" and "intense" the way a human listener instantly would.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

1. Treat genre as a spectrum instead of a strict match — e.g. give partial credit to closely related genres (indie pop vs. pop) instead of scoring them identically to a completely unrelated genre.
2. Add a way to detect and flag internally contradictory profiles (e.g. "chill" mood with a high target_energy) instead of silently returning a mediocre score with no explanation of the conflict.
3. Add a minimum-relevance threshold or an explicit "no strong matches found" message for genre-absent profiles, instead of always returning a full top-5 list regardless of actual fit.


---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  

Building this project changed how I think about recommendation systems — I used to assume "the algorithm knows what I like," but writing my own scoring rules made it obvious how much of that feeling comes from a handful of simple, somewhat arbitrary weights. The most interesting discovery was the genre floor vs. mood+energy ceiling: because I chose genre match to be worth 2.0 points and mood+energy together can only reach 2.0, a genre match can never lose to a great mood/energy match, no matter how good the fit is otherwise. That's not a bug — it's a value judgment I baked in without fully realizing it, and it made me think about how real platforms make similarly invisible choices about what "good" recommendations mean.