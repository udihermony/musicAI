# musicAI

Composing music as **code**. Each piece is a small Python script that writes a
standard MIDI file; from there you can play it through GarageBand (or any synth),
stream it live, or engrave it as sheet music. It's a playground for working on
music *with an LLM in the loop* — the script is the score, so a model (or you)
can edit individual parts, hear the result, and review changes as diffs.

> **For the next assistant:** read this file first, then the per-piece write-ups
> in [`songs/`](songs/). Favor musically interesting results and clear, readable
> scripts over abstraction. When asked for a new piece, propose the musical plan
> (key, mood, tempo, meter, harmony, the "hook") *before* writing code, and lead
> with concrete music-theory reasoning when asked what would be interesting.

## Layout

```
musicAI/
├── README.md            ← you are here
├── requirements.txt
├── to_sheet.py          # shared tool: engrave note-data (or a .mid) → MusicXML/PDF
├── play_live.py         # shared tool: stream any .mid live to GarageBand over IAC
├── pieces/              # the compositions — one self-contained script each
│   ├── jazz_progression.py   jazz_full.py   jazz_with_drums.py   jazz_blues.py
│   ├── fur_elise.py          # classical melody study
│   ├── jazz_electronic.py    # 16-bar A/B jazz-electronic with a 3-against-4 arp
│   └── nocturne.py           # original solo-piano Nocturne in E minor (+ engraving)
└── songs/               # human/LLM-readable write-ups, one per notable piece
    ├── jazz_electronic.md
    └── nocturne.md
```

The jazz scripts build on each other (`jazz_blues` → `jazz_full` / `jazz_with_drums`
→ `jazz_progression`), which is why they live together in `pieces/`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

- **Always run Python as `.venv/bin/python`**, from the **repo root**.
- macOS only for live play and engraving: live MIDI uses Apple's **IAC Driver**;
  PDF engraving uses **MuseScore 4** (the app, called headlessly).

## The three things you can do

### 1. Compose → MIDI
```bash
.venv/bin/python pieces/nocturne.py        # writes nocturne.mid (+ a summary)
```
Then drag the `.mid` into GarageBand. GarageBand splits the MIDI channels onto
separate tracks, so each instrument gets its own sound — this is the full-mix path.

### 2. Play live over IAC (no exporting)
```bash
.venv/bin/python play_live.py nocturne.mid --loop -i 4
```
Streams all tracks in real time to the IAC bus. Enable it once in **Audio MIDI
Setup → MIDI Studio → IAC Driver → "Device is online,"** and record-enable /
monitor the GarageBand track so incoming notes sound.
**Caveat:** one GarageBand instrument track plays *everything* through a single
sound. For a true multi-timbral mix, prefer the export path (or make four tracks
each filtered to one MIDI channel). For a solo-piano piece like the nocturne,
live play is exactly right.

### 3. Engrave → sheet music
```bash
.venv/bin/python pieces/nocturne.py --sheet   # writes nocturne.musicxml + nocturne.pdf
.venv/bin/python to_sheet.py jazz_electronic.mid   # rough notation straight from a .mid
```
`to_sheet.py` engraves from the **source note data** (clean rhythms/accidentals)
via its `Sheet` builder API, or quick-and-dirty from a finished `.mid`. See
[Adding a score](#adding-a-score-to-a-piece) below.

## House conventions (how a piece is built)

- `TICKS_PER_BEAT` (often `TPB`) = **480**. Express durations in ticks; derive
  sixteenth/eighth/etc. as named constants.
- Build each instrument as its own `MidiTrack`: collect absolute-time note events,
  sort them, then convert to delta times when writing. (See `build_track` in
  `pieces/jazz_electronic.py` and `pieces/nocturne.py` — the cleanest versions.)
- **One channel per instrument. Drums always on channel 9** (GM channel 10),
  using the General MIDI percussion map (kick 36, snare 38, clap 39, closed hat
  42, open hat 46, shaker 70, …).
- `program_change` is a hint for GM synths; GarageBand ignores it and uses the
  track's assigned instrument. Sustain pedal = CC 64.
- Each script's `__main__` prints a short human summary (bars, tempo, progression,
  track list, and how to assign instruments in GarageBand).
- Comment the **musical intent** (voicing degrees, why a chord is there), not the
  mechanics of mido.

## Adding a score to a piece

Engrave from the source data so notation stays in sync with the audio. Pattern
(see `build_sheet()` in `pieces/nocturne.py`):

```python
from to_sheet import Sheet                  # repo root must be importable
sh = Sheet("Title", subtitle="…", time_signature="6/8", key_sig="e",
           tempo=("Andante", 76))
rh, lh = sh.part("treble"), sh.part("bass")
rh.dyn("mp"); rh.note(71, 1.5); rh.note(67, 0.5)   # durations are quarterLengths
lh.note(40, 0.5); lh.chord([40, 47, 52], 3.0, fermata=True)
sh.render("title")                          # → title.musicxml + title.pdf
```
A piece in `pieces/` reaches the root tool with a one-line `sys.path` insert at
the top (see `nocturne.py`). MuseScore is flaky headless, so `to_sheet` retries a
few times and always writes the MusicXML even if PDF rendering fails.

## Pieces

| Piece | What it is | Write-up |
|---|---|---|
| `jazz_progression` → `jazz_full` → `jazz_with_drums` → `jazz_blues` | progressive jazz sketches (chords → arrangement → drums → 12-bar blues) | — |
| `fur_elise` | classical melody + sustained-bass study | — |
| `jazz_electronic` | 16-bar A/B jazz-electronic; 3-against-4 polyrhythmic arp; B-section planes maj7♯11 over an A drone | [songs/jazz_electronic.md](songs/jazz_electronic.md) |
| `nocturne` | original solo-piano Nocturne in E minor ("Lamplight"), ternary form, engraved score | [songs/nocturne.md](songs/nocturne.md) |

## Generated files

Running the scripts produces `.mid`, `.musicxml`, and `.pdf` artifacts in the repo
root. The deliverables (`.mid` / `.pdf` / `.musicxml`) are committed; heavy or
throwaway renders (`.png`, `.wav`, the `.venv`) are git-ignored. Everything
regenerates from source with the commands above.

## Dependencies

`mido` (MIDI I/O) · `python-rtmidi` (live ports) · `music21` (notation) ·
**MuseScore 4** for PDF · macOS **IAC Driver** for live play.
