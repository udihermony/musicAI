"""Custom track builders for jazz_electronic.

Called by render.py when it finds this file. Must expose:
    render(d) -> list[MidiTrack]

The three tracks here are algorithmic — they can't be expressed as a lookup
table in data.yaml:
  keys_events  — Rhodes comp switches between syncopated hits (figure bars)
                 and a sustained pad (drone bars) based on chord["style"].
  bass_events  — synth bass either holds a pedal (drone) or runs a syncopated
                 figure with octave jumps (figure).
  arp_events   — 3-against-4 polyrhythm: one note every dotted-eighth, cycling
                 chord-tone pools that shift each bar. The phase drift is the
                 whole hook and can't be pre-computed from static step positions.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib.music import (note_to_midi, notes_to_midi, ql, note_on,
                       build_track, expand_drum_pattern)

S = 480 // 4   # one sixteenth in ticks


def keys_events(d):
    bar  = ql(4)
    comp = [(c[0], c[1]) for c in d["patterns"]["keys_comp"]]
    ch   = d["channels"]["keys"]
    ev   = []
    for i, chord in enumerate(d["chords"]):
        base    = i * bar
        voicing = notes_to_midi(chord["voicing"])
        if chord["style"] == "drone":
            for m in voicing:
                note_on(ev, base, m, bar, 70, ch=ch)
        else:
            for start, dur in comp:
                vel = 78 if start == 0 else 68
                for m in voicing:
                    note_on(ev, base + start, m, dur, vel, ch=ch)
    return ev


def bass_events(d):
    bar = ql(4)
    fig = d["patterns"]["bass_figure"]
    ch  = d["channels"]["bass"]
    ev  = []
    for i, chord in enumerate(d["chords"]):
        base = i * bar
        root = note_to_midi(chord["bass"])
        if chord["style"] == "drone":
            note_on(ev, base, root, bar, 88, ch=ch)
        else:
            for pos, length, octv in fig:
                vel = 100 if pos == 0 else 84
                note_on(ev, base + pos * S, root + octv, length * S, vel, ch=ch)
    return ev


def arp_events(d):
    bar   = ql(4)
    step  = d["patterns"]["arp_step_ticks"]
    dur   = d["patterns"]["arp_note_dur_ticks"]
    total = len(d["chords"]) * bar
    ch    = d["channels"]["arp"]
    ev    = []
    t = idx = 0
    while t < total:
        i       = min(t // bar, len(d["chords"]) - 1)
        voicing = notes_to_midi(d["chords"][i]["voicing"])
        pool    = voicing + [voicing[0] + 12, voicing[1] + 12]
        vel     = 90 if t % bar == 0 else 74
        note_on(ev, t, pool[idx % len(pool)], min(dur, total - t), vel, ch=ch)
        idx += 1
        t   += step
    return ev


def render(d):
    ch   = d["channels"]
    pr   = d["programs"]
    fill = d["drums"].get("fill", {})
    drums = expand_drum_pattern(
        d["drums"], len(d["chords"]), ql(4),
        swing_ticks=d["drums"]["swing_ticks"],
        fill_every=fill.get("every_n_bars"),
        fill_notes=fill or None,
    )
    return [
        build_track(keys_events(d), "Rhodes",     pr["keys"], ch["keys"], tempo_bpm=d["tempo"]),
        build_track(bass_events(d), "Synth Bass", pr["bass"], ch["bass"]),
        build_track(arp_events(d),  "Poly Arp",   pr["arp"],  ch["arp"]),
        build_track(drums,          "Drums",       channel=ch["drums"]),
    ]
