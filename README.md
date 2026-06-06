# musicAI

Composing music as **code + data**. Musical content lives in YAML; a shared
library renders it to MIDI, sheet music, or live audio. Designed for working
with an LLM in the loop — edit the YAML, hear the result, review the diff.

> **For the next assistant:** read this file first, then open the relevant
> project folder (`projects/<name>/`) and read its `notes.md`. Favor musically
> interesting results over abstraction. Propose the musical plan (key, mood,
> tempo, harmony, the "hook") *before* writing anything, and lead with concrete
> music-theory reasoning when asked what would be interesting.

## Layout

```
musicAI/
├── README.md            ← you are here
├── requirements.txt
├── render.py            # render any project: render.py <name> [--sheet] [--all]
├── play_live.py         # stream any .mid live to GarageBand over IAC
├── to_sheet.py          # engrave note-data (or a .mid) → MusicXML/PDF
├── lib/
│   └── music.py         # note parsing, tick math, MIDI builders, track types
├── projects/            # one folder per composition
│   ├── nocturne/
│   │   ├── data.yaml    # all musical content (voicings, melodies, score)
│   │   └── notes.md     # write-up + LLM context for this piece
│   ├── jazz_electronic/
│   │   ├── data.yaml
│   │   ├── notes.md
│   │   └── custom.py    # algorithmic tracks (polyrhythmic arp, drone logic)
│   └── jazz_blues/  jazz_full/  jazz_with_drums/  jazz_progression/  fur_elise/
│       ├── data.yaml
│       └── notes.md
└── output/              # everything generated (.mid/.musicxml/.pdf) — git-ignored
```

**The unit of work is a project folder.** When collaborating with an LLM on a
piece, point it at `projects/<name>/` — the YAML is the score and `notes.md` is
the session context.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

- **Always run Python as `.venv/bin/python`**, from the **repo root**.
- macOS only: live MIDI uses Apple's **IAC Driver**; PDF engraving uses
  **MuseScore 4** (called headlessly).

## The three things you can do

### 1. Compose → MIDI
```bash
.venv/bin/python render.py nocturne          # one project → output/nocturne.mid
.venv/bin/python render.py --all             # every project at once
```
Then drag the `.mid` into GarageBand. GarageBand splits MIDI channels onto
separate tracks, so each instrument gets its own sound.

### 2. Play live over IAC (no exporting)
```bash
.venv/bin/python play_live.py nocturne.mid --loop -i 4
```
Streams all tracks in real time to the IAC bus. Enable the IAC Driver once in
**Audio MIDI Setup → MIDI Studio → IAC Driver → "Device is online."**
Bare filenames resolve to `output/` automatically.

### 3. Engrave → sheet music
```bash
.venv/bin/python render.py --sheet nocturne      # output/nocturne.pdf + .musicxml
.venv/bin/python to_sheet.py output/nocturne.mid # rough quantized notation
```
`--sheet` engraves from the YAML source data (clean rhythms and accidentals).
Any project whose tracks use standard types gets a score for free — just add
`key:`, `tempo_marking:`, and `clef:` fields (see nocturne as the reference).

## How pieces are built

### Standard pieces (YAML only)
All musical content in `data.yaml`, rendered entirely by `render.py`:

```yaml
title: My Piece
tempo: 120
key: e
tracks:
  - name: Melody
    type: sequential_melody   # ordered note/rest sequence
    clef: treble
    notes: [[E5, 0.5], [D#5, 0.25], ...]

  - name: Bass
    type: sustained_notes     # held notes
    clef: bass
    notes: [[A2, 1.5], ...]
```

**Available track types:**

| `type` | What it does |
|---|---|
| `block_chords` | All chord notes together for N beats; loops the progression |
| `walking_bass` | One note per beat with articulation gap; loops |
| `drum_grid` | Step-grid pattern (0-based 16th indices); `hits:` list |
| `sequential_melody` | Ordered `[note_or_null, quarter_length]` entries |
| `sustained_notes` | Each entry held for its full duration |
| `scored_melody` | Melody from a `{bar_ref: notes}` dict, arranged by a `score:` list |
| `arpeggio_lh` | Chord voicings expanded via an index `pattern:`, with optional sustain pedal |

`drum_grid` is skipped by the sheet engraver. All other types produce notation.

### Custom pieces (YAML + custom.py)
If a project has `custom.py`, `render.py` calls its `render(d) → [MidiTrack, …]`
function instead of the generic dispatcher. Use this only when tracks are
*computed* rather than looked up — `jazz_electronic` is the current example
(polyrhythmic arp, per-chord drone/comp switching).

## Adding a new project

**Standard piece (YAML only):**
1. Create `projects/my_piece/data.yaml` with `title`, `tempo`, `tracks:`.
2. Run `render.py my_piece`.
3. Add `projects/my_piece/notes.md` with context for future sessions.
4. Add `key:` and `clef:` fields to enable `--sheet`.

**Custom piece:**
Same as above, plus `projects/my_piece/custom.py` exposing `render(d)`.

## Note format

Notes use scientific pitch: `C4` = middle C = MIDI 60. Sharps: `C#4`, `D#5`.
Flats: `Bb3`, `Eb4`. Rests: `null`. Durations are **quarter-lengths**:
`0.25` = 16th, `0.5` = eighth, `1.0` = quarter, `1.5` = dotted quarter.

## Projects

| Project | Style | Tracks | Notes |
|---|---|---|---|
| `jazz_progression` | ii–V–I sketch | chords | — |
| `jazz_with_drums` | ii–V–I + swing kit | chords, drums | — |
| `jazz_full` | ii–V–I full band | chords, walking bass, drums | — |
| `jazz_blues` | 12-bar F blues | chords, walking bass, drums | — |
| `fur_elise` | Classical melody study | melody, bass | A section only |
| `jazz_electronic` | 16-bar A/B jazz-electronic | Rhodes, synth bass, poly arp, drums | custom.py |
| `nocturne` | Original piano nocturne | Piano RH, Piano LH | score available |

## Dependencies

`mido` · `python-rtmidi` · `music21` · `pyyaml` · **MuseScore 4** (PDF) · macOS **IAC Driver** (live)
