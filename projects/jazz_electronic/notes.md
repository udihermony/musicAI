# jazz_electronic

**Script:** `jazz_electronic.py` → **`jazz_electronic.mid`**
**Form:** 16 bars, A/B · **Key:** A minor (modal) · **Meter:** 4/4 · **Tempo:** 84 BPM · **Length:** ~45.7s

A dark, hypnotic jazz-electronic piece "a bit experimental." Extended jazz
harmony (9ths, ♯11s, altered dominants) on an electric-piano/synth palette, with
one structural idea carried all the way through: a polyrhythmic arp that never
lines up with the beat.

## The hook — a 3-against-4 polyrhythm

The arp ("Poly Arp" track) fires **one note every dotted-eighth** (360 ticks)
while the drums hold a straight 4/4. Three arp notes span two beats, so the
pattern phases against the grid and lands in a different spot every bar — the
loop keeps moving without ever repeating where the ear expects. It draws its
notes from whatever chord is current, so the phasing line is always consonant
with the harmony underneath.

## Harmony

```
A (bars 1-8):   Am9   Am9   Dm9   Dm9   Bbmaj7#11   Fmaj9   E7b9   E7b9
B (bars 9-16):  Bbmaj7#11/A  Cmaj7#11/A  Dbmaj7#11/A  Cmaj7#11/A  Bbmaj7#11/A  Abmaj7#11/A  Cm9  Bb13
                └──────────────── A pedal · maj7#11 planed ────────────────┘   └─ turnaround ─┘
```

**A section** — `i – iv – ♭II – ♭VI – V7♭9` in A aeolian. Everything leans to the
flat side and resolves inward: dark and closed. The `B♭maj7♯11` (bar 5) is the
chromatic-mediant splash of color; `E7♭9` is the altered dominant slamming home.
Rhodes plays rootless/extended voicings with a syncopated two-hit comp (beat 1,
pushed again on the "and of 3"); the synth bass runs an active, octave-jumping
figure.

**B section — the development.** The bass drops to a **low A drone** and a single
`maj7♯11` shape *planes* over it in parallel motion, arcing out to dissonance and
back: `B♭ → C → D♭ → C → B♭ → A♭`, all over the held A. Function dissolves into
pure color — `C/A` reads bright (it's really Am13), while `D♭/A` and `A♭/A` are
the deliberate crunch (E♭ grinding against the A). The texture flips with it: the
Rhodes switches from comping to a sustained **pad**, the bass from riffing to a
held pedal. Then bars 15–16 lift off the drone for a chromatic **tritone-sub
turnaround**, `Cm9 → B♭13`, walking the bass `C → B♭ → A` smoothly back to the
top instead of using the A-section's V7.

## Instrumentation (4 tracks)

| # | Track       | Ch | Suggested GarageBand sound      |
|---|-------------|----|---------------------------------|
| 1 | Rhodes      | 0  | Electric piano / Rhodes         |
| 2 | Synth Bass  | 1  | Synth bass (sub-y)              |
| 3 | Poly Arp    | 2  | Bright saw or pluck lead        |
| 4 | Drums       | 9  | Electronic kit (GM ch 10)       |

Drums: syncopated kick (1, &2, &3), backbeat snare + layered clap, ghost snare,
swung 8th-note hats, an open-hat push into each bar, a 16th-note shaker bed, and
a snare fill into each section turnaround.

## How to hear it

- **Full mix:** run `.venv/bin/python pieces/jazz_electronic.py`, drag `output/jazz_electronic.mid`
  into GarageBand, assign the four instruments above.
- **Live audition:** `.venv/bin/python play_live.py jazz_electronic.mid --loop -i 4`
  (see `CONTEXT.md` for the IAC setup and the single-instrument caveat).

The moment to listen for: **bar 9**, where the groove keeps driving but the
harmony stops resolving and just glides over the drone.

## Possible next moves (not yet done)

- Octave-displace the arp in the B section to spotlight the planing.
- Push further out: an odd-meter bridge (7/8), or a major-thirds/Coltrane axis
  insert as a 2-bar surprise.
