# Nocturne in E minor — "Lamplight"

**Script:** `nocturne.py` → **`nocturne.mid`**
**Form:** 28 bars, ternary A–B–A′ + coda · **Key:** E minor → Picardy E major · **Meter:** 6/8 · **Tempo:** ♩=76 (Andante) · **Length:** ~1:06

An original solo-piano character piece — a Romantic nocturne. A singing
right-hand melody over a rocking left-hand broken-chord arpeggio, pedaled each
bar. Solo piano: both hands are on channel 0, so it plays through one instrument.

## Form & harmony

```
A    (1-8):   Em  Em/D#  Em/D  Em/C#  Cmaj7  B7  Em  D7
B    (9-16):  G   D/F#   Em7   C      Am7    D7  G   B7
A'   (17-24): Em  Em/D#  Em/D  Em/C#  Cmaj7  B7  Em  B7b9
coda (25-28): Em  Cmaj7  B7  E
```

- **A — the line cliché.** The spine of the opening is a chromatically
  descending bass under a held Em color: `E → D♯ → D → C♯ → C → B`
  (Em → Em(maj7) → Em7 → Em6 → Cmaj7 → B7). The right hand sings four-bar
  arches in the upper register; bar 8 turns to **D7** to pivot brightward.
- **B — relative major.** Lifts to **G major** with more flowing running
  eighths and a `ii–V–I` (Am7 → D7 → G). Bar 16's surprise **B7** (the I chord's
  third, B, reinterpreted as a dominant root) yanks the music back home for A′.
- **A′ — varied return.** Restates the opening melody a touch louder/fuller,
  then a fresh cadence through **B7♭9** (the C♮ ninth is the ache) into the coda.
- **Coda — Picardy.** Settles down and ends on **E major** instead of minor — a
  warm glow rather than a dark close.

## Texture & performance details

- **Left hand:** per bar, `[bass] + four ascending chord tones` played in the
  contour `0 1 2 3 4 3` across the six eighths — a rocking arpeggio that rises
  and eases back to lead into the next bar's bass.
- **Sustain pedal** (CC64) is re-struck every bar: down on the downbeat, up just
  before the next, so each harmony rings cleanly without blurring into the next.
- **Dynamics** shift by section: A mp, B brighter, A′ fuller, coda hushed; the
  final E5 is voiced soft.
- **Final bar** rolls the E-major chord (staggered onsets) and holds it under
  pedal.

## How to hear it (and see it)

- **Full mix:** `.venv/bin/python pieces/nocturne.py`, drag `output/nocturne.mid`
  into GarageBand, assign a single **Grand Piano** to both tracks.
- **Live audition:** `.venv/bin/python play_live.py nocturne.mid -i 4`
  (a single piano instrument is exactly right here — no multi-timbral caveat,
  since the whole piece is one instrument on channel 0).
- **Sheet music:** `.venv/bin/python pieces/nocturne.py --sheet` writes
  `nocturne.musicxml` + `nocturne.pdf` (grand staff, engraved from the same note
  data via `to_sheet.py`, so the score always matches the audio). Open the PDF to
  print, or the MusicXML in MuseScore to tweak layout.

## Possible next moves (not yet done)

- Add a second contrasting episode (a C-section) for a rondo, or repeat A with
  written-out ornamentation.
- Voice the A′ melody in octaves / add an inner voice for a richer return.
- A written ritardando into the coda (stretch the final bars' note timings).
