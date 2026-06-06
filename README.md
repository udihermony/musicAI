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
├── lib/
│   └── music.py         # shared lib: note parsing, tick math, MIDI event building
├── data/                # all musical content — edit these to change the music
│   ├── jazz_progression.yaml  jazz_full.yaml  jazz_with_drums.yaml  jazz_blues.yaml
│   ├── fur_elise.yaml
│   ├── jazz_electronic.yaml   # chords, voicings, patterns, drum hits
│   └── nocturne.yaml          # voicings, per-bar melodies, score sequence
├── pieces/              # thin scripts: load YAML → call lib → write MIDI
│   ├── jazz_progression.py   jazz_full.py   jazz_with_drums.py   jazz_blues.py
│   ├── fur_elise.py
│   ├── jazz_electronic.py
│   └── nocturne.py           # add --sheet to also engrave a PDF score
├── songs/               # human/LLM-readable write-ups, one per notable piece
│   ├── jazz_electronic.md
│   └── nocturne.md
└── output/              # everything generated (.mid/.musicxml/.pdf) — git-ignored
```

All scripts write their artifacts to `output/`, which is git-ignored — the tracked
repo stays source-only. Regenerate anything by re-running its script.

**To change the music:** edit the relevant `data/*.yaml` file and re-run the piece.
No Python knowledge needed for most musical edits (changing a chord, transposing a
note, adjusting tempo or velocity, tweaking a rhythm pattern).

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
.venv/bin/python pieces/nocturne.py        # writes output/nocturne.mid (+ a summary)
```
Then drag the `.mid` into GarageBand. GarageBand splits the MIDI channels onto
separate tracks, so each instrument gets its own sound — this is the full-mix path.

### 2. Play live over IAC (no exporting)
```bash
.venv/bin/python play_live.py nocturne.mid --loop -i 4   # bare names resolve to output/
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
.venv/bin/python pieces/nocturne.py --sheet      # output/nocturne.musicxml + .pdf
.venv/bin/python to_sheet.py output/jazz_electronic.mid   # rough notation from a .mid
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

Everything the scripts produce (`.mid`, `.musicxml`, `.pdf`) goes into `output/`,
which is git-ignored — so the tracked repo is source-only and the working tree
stays clean. Regenerate any artifact by re-running its script (or `--sheet`).
`play_live.py` and `to_sheet.py` accept bare names and look in `output/`.

## Dependencies

`mido` (MIDI I/O) · `python-rtmidi` (live ports) · `music21` (notation) ·
**MuseScore 4** for PDF · macOS **IAC Driver** for live play.
