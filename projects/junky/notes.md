# Junky

**Style:** funky jazz — dark, syncopated, tight pocket
**Key:** D minor / D Dorian · **Tempo:** 92 BPM · **Meter:** 4/4
**Status:** iteration 2 — drums + bass

## The groove concept

The name is the vibe: greasy, slightly off-kilter, deeply in the pocket.
Think early-70s Miles Davis electric period meets a funk rhythm section.
Dark harmonically, syncopated rhythmically, sparse and deliberate.

## Drum track

The kick is the hook. Three ideas stacked:

1. **Anchors on 1 and 3** (velocity 115) — you always know where the bar is
2. **"a-of-1" push** (step 3) — anticipates beat 2, creates forward motion
3. **"and-of-4" push** (step 14) — drives back into beat 1 of the next bar

Snare on the backbeat (2 and 4), plus a bed of **ghost notes** at velocity 30
on steps 2, 6, 9, 11, 13, 15. Light 8th-note swing (30 ticks) on "and" positions.
**Cowbell** on beats 1 and 3. Snare fill escalating into bars 4 and 8.

## Bass track (added iteration 2)

**D minor / D Dorian** — modal, not purely functional. The bass doesn't spell
out changes; it creates texture and rhythm.

Two-bar pattern looped 4×. The two bars have different characters:

**Bar A (question)** — dense, locks with the kick on *all five* kick positions:
```
beat 1:     D2 (8th)          — anchor
a-of-1:     D2 (16th)         — THE KEY LOCK with kick step 3
beat 2:     F2 (8th)          — minor 3rd, under snare
and-of-2:   G2 (8th)
beat 3:     D2 (8th)          — anchor
and-of-3:   A2 (8th)          — 5th, lock with kick
beat 4:     D3 (8th)          — OCTAVE JUMP — the funk hook
and-of-4:   C3 (8th)          — minor 7th, lock with kick + open hat
```

**Bar B (answer)** — more space, rests create contrast:
```
beat 1:     D2 (dotted 8th)   — sits longer
a-of-1:     A2 (16th)         — 5th instead of root, unexpected
beat 2:     F2 (8th)
and-of-2:   REST              — big space
beat 3:     D2 (8th)
and-of-3:   REST              — kick hits but bass rests (contrast)
a-of-3:     G2 (16th)
beat 4:     C3 (8th)          — tritone tension (C vs D root area)
and-of-4:   A2 (8th)          — dominant pull back to D
```

`articulation: 0.75` — each note sounds for 75% of its slot, keeping it tight
and percussive (funky bass never sustains).

## Possible next moves (in order of impact)

1. **Rhodes / chord stabs** — sparse voicings, pushing on the off-beats.
   Suggested: Dm9 (D F A C E) and Gm9 (G Bb D F A), rootless, mid register.
   One or two stabs per bar on e-of-2 and a-of-3 (steps 5 and 11).
   Don't over-voice — space is the point.

2. **Lead line** — a short modal phrase (D Dorian: D E F G A B C) that enters
   every 4 bars. Sparse and conversational, not a melody. Could be Rhodes right
   hand, muted trumpet, or flute.

3. **Bass variation in bars 5-8** — currently the 2-bar pattern repeats
   identically all 8 bars. Bars 5-8 could shift the root to G (iv chord, Gm7)
   for 2 bars before returning to Dm — needs custom.py or a longer notes list.

4. **Drum variation** — after bar 4, vary the kick (add step 6, remove step 10)
   for a different flavour in the second half. Requires custom.py.

## Track layout (GarageBand)

| Track | Channel | Instrument |
|---|---|---|
| Drums | 9 (GM) | Electronic / hybrid drum kit |
| Bass | 1 | Electric bass or Fender Rhodes bass |
