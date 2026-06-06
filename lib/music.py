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

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ_DIR  = os.path.join(ROOT, "projects")
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
    """Load data.yaml from projects/<name>/data.yaml."""
    path = os.path.join(PROJ_DIR, name, "data.yaml")
    with open(path) as f:
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
    "low_tom":     41, "mid_tom":    45, "high_tom":  48,
    "ride":        51, "crash":      49, "ride_bell": 53,
    "cowbell":     56, "shaker":     70, "tambourine": 54,
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


# ---------------------------------------------------------------------------
# Generic track builders — keyed by YAML `type:` field.
# Each takes: td (track dict), d (global piece dict), plus keyword args.
# `first=True` embeds tempo + time_signature metadata in that track.
# ---------------------------------------------------------------------------

def _meta(td, d, first):
    """Return kwargs for build_track that carry metadata only on the first track."""
    if not first:
        return {}
    out = {"tempo_bpm": d["tempo"]}
    ts = d.get("time_signature")
    if ts:
        out["time_sig"] = ts
    return out


def build_block_chords(td, d, loops=1, first=False):
    """Play all chord notes simultaneously for their duration. Loops the progression."""
    ch  = td.get("channel", 0)
    vel = td.get("velocity", d.get("velocity", 80))
    default_beats = td.get("beats_per_chord", d.get("beats_per_chord", 4))
    prog = td.get("progression", d.get("progression", []))
    ev = []
    t = 0
    for _ in range(loops):
        for chord in prog:
            dur = ql(chord.get("beats", default_beats))
            for m in notes_to_midi(chord["notes"]):
                note_on(ev, t, m, dur, vel, ch=ch)
            t += dur
    return build_track(ev, td.get("name", "Chords"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


def build_walking_bass(td, d, loops=1, first=False):
    """One note per beat with a short articulation gap. Loops the bar list."""
    ch      = td.get("channel", 1)
    vel     = td.get("velocity", d.get("velocity", 85))
    gap     = td.get("note_gap", 20)
    bars    = td.get("bars", [])
    beat    = ql(1.0)
    dur     = beat - gap
    ev = []
    t = gap
    for _ in range(loops):
        for bar in bars:
            for pitch in bar:
                note_on(ev, t, note_to_midi(pitch), dur, vel, ch=ch)
                t += beat
    return build_track(ev, td.get("name", "Walking Bass"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


def build_drum_grid(td, d, n_bars=1, first=False):
    """Step-grid drum pattern. n_bars is the total bar count (loops already applied)."""
    bar_ticks = ql(4)   # assumes 4/4; override via td["bar_beats"] if needed
    if "bar_beats" in td:
        bar_ticks = ql(td["bar_beats"])
    fill = td.get("fill")
    ev = expand_drum_pattern(
        td, n_bars, bar_ticks,
        swing_ticks=td.get("swing_ticks", 0),
        fill_every=fill.get("every_n_bars") if fill else None,
        fill_notes=fill if fill else None,
    )
    return build_track(ev, td.get("name", "Drums"),
                       channel=td.get("channel", 9), **_meta(td, d, first))


def build_sequential_melody(td, d, loops=1, first=False):
    """Ordered list of [note_or_null, quarter_length] entries. Rests on null.

    articulation (0.0-1.0): fraction of the slot the note sounds — 1.0 is
    fully legato, 0.75 is punchy (good for funk bass), 0.5 is staccato.
    """
    ch          = td.get("channel", 0)
    vel         = td.get("velocity", d.get("melody_velocity", 80))
    articulation = td.get("articulation", 1.0)
    ev = []
    t = 0
    for _ in range(loops):
        for entry in td.get("notes", []):
            pitch, dur_ql = entry
            slot     = ql(dur_ql)
            sounding = max(1, int(slot * articulation))
            if isinstance(pitch, list):           # chord — list of note names
                for p in pitch:
                    m = note_to_midi(p)
                    if m is not None:
                        note_on(ev, t, m, sounding, vel, ch=ch)
            else:
                m = note_to_midi(pitch)
                if m is not None:
                    note_on(ev, t, m, sounding, vel, ch=ch)
            t += slot
    return build_track(ev, td.get("name", "Melody"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


def build_sustained_notes(td, d, loops=1, first=False):
    """Each entry is [note, quarter_length] — held for its full duration."""
    ch  = td.get("channel", 1)
    vel = td.get("velocity", d.get("bass_velocity", 70))
    ev = []
    t = 0
    for _ in range(loops):
        for entry in td.get("notes", []):
            pitch, dur_ql = entry
            dur = ql(dur_ql)
            note_on(ev, t, note_to_midi(pitch), dur, vel, ch=ch)
            t += dur
    return build_track(ev, td.get("name", "Bass"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


_DYN_VEL = {
    "ppp": 35, "pp": 45, "p": 58, "mp": 72,
    "mf": 82, "f": 92, "ff": 104, "fff": 115,
}


def _vel_at(dyn_map, bar_index, fallback=72):
    """Return velocity for bar_index given a {bar_index: dynamic_label} dict."""
    vel = fallback
    for k in sorted(int(k) for k in dyn_map):
        if bar_index >= k:
            vel = _DYN_VEL.get(str(dyn_map[k]), fallback)
    return vel


def build_scored_melody(td, d, loops=1, first=False):
    """Melody stored as a {bar_ref: [(note, ql)]} dict, arranged by a score list.

    score is a list of [chord_name, melody_ref] pairs (chord_name is ignored here —
    it belongs to the accompaniment track). dynamics is a {bar_index: label} map.
    velocity_offset is added to the section velocity (use a positive number for RH).
    """
    melodies   = {int(k): v for k, v in
                  (td.get("melodies") or d.get("melodies", {})).items()}
    score      = td.get("score") or d.get("score", [])
    dyn_map    = td.get("dynamics") or d.get("dynamics", {})
    ch         = td.get("channel", 0)
    vel_offset = td.get("velocity_offset", 0)
    last       = len(score) - 1
    ev         = []
    t          = 0
    for i, (_, mel_ref) in enumerate(score):
        vel = _vel_at(dyn_map, i) + vel_offset
        for entry in melodies[int(mel_ref)]:
            pitch, dur_ql = entry
            dur = ql(dur_ql)
            m   = note_to_midi(pitch)
            if m is not None:
                note_on(ev, t, m, dur, 66 if i == last else vel, ch=ch)
            t += dur
    return build_track(ev, td.get("name", "Melody"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


def build_arpeggio_lh(td, d, loops=1, first=False):
    """Chord voicings expanded as arpeggios via an index pattern, with sustain pedal.

    voicings: {chord_name: {bass: note, upper: [notes]}}
    score:    [[chord_name, any], ...]   (second element ignored)
    pattern:  list of int indices into [bass, u0, u1, u2, u3, ...]
    pedal:    true → emit CC64 sustain down/up each bar
    velocity_offset: subtract from section velocity for a softer LH (use negative).
    On the final bar, the chord is rolled (staggered note onsets).
    """
    voicings   = td.get("voicings") or d.get("voicings", {})
    score      = td.get("score") or d.get("score", [])
    pattern    = td.get("pattern") or d.get("lh_arpeggio", [])
    dyn_map    = td.get("dynamics") or d.get("dynamics", {})
    ch         = td.get("channel", 0)
    pedal      = td.get("pedal", False)
    vel_offset = td.get("velocity_offset", 0)
    ts         = d.get("time_signature", [4, 4])
    bar_ticks  = ql(ts[0] * (4 / ts[1]))
    step_ticks = bar_ticks // max(len(pattern), 1)
    last       = len(score) - 1
    ev         = []
    for i, (chord_name, _) in enumerate(score):
        base  = i * bar_ticks
        v     = voicings[chord_name]
        arp   = [note_to_midi(v["bass"])] + notes_to_midi(v["upper"])
        vel   = _vel_at(dyn_map, i) + vel_offset
        if pedal:
            cc(ev, base,            64, 127, ch=ch)
            cc(ev, base + bar_ticks - 15, 64, 0, ch=ch)
        if i == last:
            for j, m in enumerate(arp):
                note_on(ev, base + j * 30, m, bar_ticks - j * 30, vel + 4, ch=ch)
        else:
            for step, idx in enumerate(pattern):
                v_note = vel + (8 if idx == 0 else 0)
                note_on(ev, base + step * step_ticks, arp[idx], step_ticks, v_note, ch=ch)
    return build_track(ev, td.get("name", "Accompaniment"),
                       program=td.get("program"), channel=ch, **_meta(td, d, first))


# Map type strings to builder functions (used by render.py)
TRACK_BUILDERS = {
    "block_chords":      build_block_chords,
    "walking_bass":      build_walking_bass,
    "drum_grid":         build_drum_grid,
    "sequential_melody": build_sequential_melody,
    "sustained_notes":   build_sustained_notes,
    "scored_melody":     build_scored_melody,
    "arpeggio_lh":       build_arpeggio_lh,
}
