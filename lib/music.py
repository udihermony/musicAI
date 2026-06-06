"""Shared music utilities: note parsing, tick math, MIDI event building.

All pieces import from here; none of this is piece-specific.

Note name convention (YAML input):
  Scientific pitch — C4 = middle C = MIDI 60.
  Sharps: C#4, D#5. Flats: Bb3, Eb4. Rests: null or "rest".

Duration convention (YAML input):
  Quarter-lengths (float). 0.25 = 16th, 0.5 = eighth, 1.0 = quarter,
  1.5 = dotted quarter, 3.0 = dotted half, etc.
  lib converts to ticks using TPB=480.
"""

import os
import re
import yaml
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
OUTPUT_DIR = os.path.join(ROOT, "output")
TPB = 480  # ticks per quarter note — project-wide standard

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_SHARP_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT_NAMES  = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


# ---------------------------------------------------------------------------
# Note / pitch utilities
# ---------------------------------------------------------------------------

def note_to_midi(name):
    """Parse scientific pitch to MIDI number. 'E4'->64, 'Bb3'->46, None->None."""
    if name is None or str(name).lower() in ("rest", "none", "null"):
        return None
    m = re.match(r'^([A-G])([#b]*)(-?\d+)$', str(name).strip())
    if not m:
        raise ValueError(f"Cannot parse note name: {name!r}")
    letter, acc, octave = m.group(1), m.group(2), int(m.group(3))
    pc = _PC[letter] + acc.count("#") - acc.count("b")
    return (int(octave) + 1) * 12 + pc


def midi_to_note(midi, prefer="sharp"):
    names = _FLAT_NAMES if prefer == "flat" else _SHARP_NAMES
    return f"{names[midi % 12]}{midi // 12 - 1}"


def notes_to_midi(names):
    """Convert a list of note names to MIDI numbers."""
    return [note_to_midi(n) for n in names]


def ql(quarters, tpb=TPB):
    """Quarter-length float -> integer ticks."""
    return int(round(quarters * tpb))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load(name):
    """Load a YAML data file from data/. Pass 'piece' or 'piece.yaml'."""
    if not name.endswith(".yaml"):
        name += ".yaml"
    with open(os.path.join(DATA_DIR, name)) as f:
        return yaml.safe_load(f)


def out_path(filename):
    """Return the output/ path, creating the directory if needed."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)


# ---------------------------------------------------------------------------
# MIDI event helpers (all use absolute time; build_track sorts and deltas)
# ---------------------------------------------------------------------------

def note_on(events, t, midi, dur, vel, ch=0):
    """Append an absolute-time note_on/off pair."""
    events.append((t,       1, "on",  midi, vel, ch))
    events.append((t + dur, 0, "off", midi, 0,   ch))


def cc(events, t, control, value, ch=0):
    events.append((t, 1, "cc", control, value, ch))


def build_track(events, name, program=None, channel=0,
                tempo_bpm=None, time_sig=None):
    """Build a MidiTrack from a list of absolute-time events.

    events items: (abs_tick, sort_key, kind, a, b, ch)
      kind "on"  -> note_on  with note=a, vel=b
      kind "off" -> note_off with note=a
      kind "cc"  -> control_change control=a, value=b
    """
    track = MidiTrack()
    if tempo_bpm is not None:
        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(tempo_bpm)))
    if time_sig is not None:
        num, den = time_sig
        track.append(MetaMessage("time_signature", numerator=num, denominator=den))
    track.append(MetaMessage("track_name", name=name))
    if program is not None:
        track.append(Message("program_change", program=program, channel=channel, time=0))

    prev = 0
    for t, _, kind, a, b, ch in sorted(events, key=lambda e: (e[0], e[1])):
        delta = t - prev
        if kind == "on":
            track.append(Message("note_on",  note=a, velocity=b, time=delta, channel=ch))
        elif kind == "off":
            track.append(Message("note_off", note=a, velocity=0, time=delta, channel=ch))
        else:
            track.append(Message("control_change", control=a, value=b, time=delta, channel=ch))
        prev = t
    return track


def write_midi(path, tracks, tpb=TPB):
    """Write a finished MidiFile. tracks is a list of MidiTrack objects."""
    mid = MidiFile(ticks_per_beat=tpb)
    for t in tracks:
        mid.tracks.append(t)
    mid.save(path)


# ---------------------------------------------------------------------------
# Common drum expander
# ---------------------------------------------------------------------------

GM_DRUMS = {
    "kick":        36, "snare":      38, "clap":      39,
    "closed_hat":  42, "pedal_hat":  44, "open_hat":  46,
    "ride":        51, "shaker":     70,
    "low_tom":     41, "mid_tom":    45, "high_tom":  48,
}


def expand_drum_pattern(pattern_data, n_bars, bar_ticks, swing_ticks=0,
                        notes_override=None, fill_every=None, fill_notes=None):
    """Build drum events from a YAML drum pattern description.

    pattern_data keys:
      steps_per_bar: int (usually 16 for 4/4)
      hits: list of {note: <name>, steps: [ints], velocity: int}
             step positions are 0-based 16th indices
      swing_steps: list of step indices whose timing is pushed by swing_ticks
      shaker_steps: 'all' or list (shorthand for shaker on every step)
    """
    note_map = {**GM_DRUMS, **(notes_override or {})}
    steps_per_bar = pattern_data.get("steps_per_bar", 16)
    step_ticks = bar_ticks // steps_per_bar
    swing_steps = set(pattern_data.get("swing_steps", []))

    events = []
    for bar in range(n_bars):
        base = bar * bar_ticks
        is_fill = fill_every and (bar + 1) % fill_every == 0

        for hit in pattern_data.get("hits", []):
            midi = note_map[hit["note"]]
            vel = hit.get("velocity", 80)
            steps = hit.get("steps", [])

            # skip fill-replaced steps on fill bars
            fill_replaces = set(hit.get("fill_replaces", []))
            active_steps = [s for s in steps if not (is_fill and s in fill_replaces)]

            for step in active_steps:
                push = swing_ticks if step in swing_steps else 0
                t = base + step * step_ticks + push
                note_on(events, t, midi, min(step_ticks - 1, 80), vel, ch=9)

        # optional snare fill into the next section
        if is_fill and fill_notes:
            fill_steps = fill_notes.get("steps", [])
            fill_midi = note_map[fill_notes.get("note", "snare")]
            for i, step in enumerate(fill_steps):
                vel = fill_notes.get("velocity_start", 60) + i * fill_notes.get("velocity_ramp", 8)
                t = base + step * step_ticks
                note_on(events, t, fill_midi, step_ticks - 1, vel, ch=9)

    return events
