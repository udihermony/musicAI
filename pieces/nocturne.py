"""Nocturne in E minor — "Lamplight". An original solo-piano character piece.

Ternary form (A - B - A' - coda), 28 bars of 6/8 at a flowing Andante. A singing
right-hand line over a rocking left-hand broken-chord arpeggio, with the sustain
pedal re-struck each bar.

The harmonic spine of the A section is a "line cliche": an Em chord held on top
while the bass walks down chromatically E - D# - D - C# - C - B
(Em -> Em(maj7) -> Em7 -> Em6 -> Cmaj7 -> B7). B brightens to the relative G
major; the coda ends on a Picardy third (E major).

One instrument: both hands are on channel 0 — assign a single Grand Piano.
"""

import os
import sys

from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root, for to_sheet

TPB = 480
EIGHTH = TPB // 2          # 240 — the pulse of 6/8
BAR = 6 * EIGHTH           # 1440 — one 6/8 bar
TEMPO_BPM = 76             # quarter-note tempo; eighths flow at ~152/min
PIANO_PROGRAM = 0          # Acoustic Grand (a hint; GarageBand uses its own)

# Left-hand chords: name -> (bass note, [4 upper tones, ascending]).
# The A-section quartet keeps the same Em triad on top while only the bass moves.
VOICINGS = {
    "Em":     (40, [59, 64, 67, 71]),  # E2  | B3 E4 G4 B4
    "Em/D#":  (39, [59, 64, 67, 71]),  # D#2 | (maj7 in bass)
    "Em/D":   (38, [59, 64, 67, 71]),  # D2  | (m7 in bass)
    "Em/C#":  (37, [59, 64, 67, 71]),  # C#2 | (6 in bass)
    "Cmaj7":  (36, [60, 64, 67, 71]),  # C2  | C4 E4 G4 B4
    "B7":     (35, [59, 63, 66, 69]),  # B1  | B3 D#4 F#4 A4
    "D7":     (38, [57, 60, 66, 72]),  # D2  | A3 C4 F#4 C5   (V7 of G)
    "G":      (43, [59, 62, 67, 71]),  # G2  | B3 D4 G4 B4
    "D/F#":   (42, [57, 62, 66, 69]),  # F#2 | A3 D4 F#4 A4
    "Em7":    (40, [59, 62, 67, 71]),  # E2  | B3 D4 G4 B4
    "C":      (36, [60, 64, 67, 72]),  # C2  | C4 E4 G4 C5
    "Am7":    (33, [60, 64, 67, 69]),  # A1  | C4 E4 G4 A4
    "B7b9":   (35, [60, 63, 66, 69]),  # B1  | C4 D#4 F#4 A4  (b9 = C)
    "E":      (40, [56, 59, 64, 68]),  # E2  | G#3 B3 E4 G#4  (Picardy major)
}

# Right-hand melody, per bar: (midi or None for rest, duration in eighths).
# Each bar sums to 6 eighths.
M = {
    1:  [(71, 3), (67, 1), (69, 1), (71, 1)],          # B  / G A B
    2:  [(72, 3), (71, 1), (69, 1), (67, 1)],          # C5 / B A G
    3:  [(74, 3), (72, 1), (71, 1), (69, 1)],          # D5 / C B A
    4:  [(71, 3), (69, 1), (67, 1), (66, 1)],          # B  / A G F#
    5:  [(72, 3), (74, 1), (76, 1), (74, 1)],          # C5 / D E5 D
    6:  [(71, 3), (69, 1), (66, 1), (63, 1)],          # B  / A F# D#  (B7 fall)
    7:  [(76, 3), (74, 1), (72, 1), (71, 1)],          # E5 / D C B
    8:  [(69, 2), (72, 2), (74, 2)],                   # A C5 D5  (rise into G)
    9:  [(71, 1), (74, 1), (79, 2), (78, 1), (76, 1)], # B D5 G5 F#5 E5
    10: [(78, 1), (76, 1), (74, 2), (73, 1), (74, 1)], # F#5 E5 D5 C#5 D5
    11: [(76, 1), (74, 1), (71, 2), (67, 1), (69, 1)], # E5 D5 B G A
    12: [(72, 3), (76, 1), (74, 1), (72, 1)],          # C5 / E5 D5 C5
    13: [(69, 2), (72, 2), (76, 2)],                   # A C5 E5  (Am rise)
    14: [(78, 1), (76, 1), (74, 1), (72, 1), (74, 2)], # F#5 E5 D5 C5 D5
    15: [(79, 3), (78, 1), (76, 1), (74, 1)],          # G5 / F#5 E5 D5
    16: [(71, 3), (69, 1), (66, 1), (63, 1)],          # B / A F# D#  (pivot home)
    23: [(76, 3), (74, 1), (72, 1), (71, 1)],          # E5 / D C B  (A' cadence)
    24: [(72, 3), (71, 1), (69, 1), (66, 1)],          # C5(b9) / B A F#
    25: [(71, 3), (69, 1), (67, 1), (64, 1)],          # B / A G E
    26: [(67, 3), (72, 1), (71, 1), (67, 1)],          # G / C5 B G
    27: [(66, 3), (69, 1), (66, 1), (63, 1)],          # F# / A F# D#
    28: [(76, 6)],                                     # E5 held — Picardy glow
}

# Bar -> chord. A' (17-22) reuses the A melody (bars 1-6); 23-24 are a fresh cadence.
SCORE = [
    ("Em", 1), ("Em/D#", 2), ("Em/D", 3), ("Em/C#", 4),     # A
    ("Cmaj7", 5), ("B7", 6), ("Em", 7), ("D7", 8),
    ("G", 9), ("D/F#", 10), ("Em7", 11), ("C", 12),          # B (G major)
    ("Am7", 13), ("D7", 14), ("G", 15), ("B7", 16),
    ("Em", 1), ("Em/D#", 2), ("Em/D", 3), ("Em/C#", 4),     # A'
    ("Cmaj7", 5), ("B7", 6), ("Em", 23), ("B7b9", 24),
    ("Em", 25), ("Cmaj7", 26), ("B7", 27), ("E", 28),        # coda -> Picardy
]

LH_PATTERN = [0, 1, 2, 3, 4, 3]   # arpeggio contour over the 6 eighths


def note(ev, t, n, dur, vel, ch=0):
    ev.append((t, 2, "on", n, vel, ch))
    ev.append((t + dur, 0, "off", n, 0, ch))


def cc(ev, t, control, value, ch=0):
    ev.append((t, 1, "cc", control, value, ch))


def build_track(ev, name, program=None, meta=False):
    track = MidiTrack()
    if meta:
        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
        track.append(MetaMessage("time_signature", numerator=6, denominator=8))
    track.append(MetaMessage("track_name", name=name))
    if program is not None:
        track.append(Message("program_change", program=program, channel=0, time=0))

    prev = 0
    for t, _order, kind, a, b, ch in sorted(ev, key=lambda e: (e[0], e[1])):
        delta = t - prev
        if kind == "on":
            track.append(Message("note_on", note=a, velocity=b, time=delta, channel=ch))
        elif kind == "off":
            track.append(Message("note_off", note=a, velocity=0, time=delta, channel=ch))
        else:
            track.append(Message("control_change", control=a, value=b, time=delta, channel=ch))
        prev = t
    return track


def section_vel(bar_index):
    """Phrase dynamics by section (bar_index is 0-based over SCORE)."""
    if bar_index < 8:    return 82, 52    # A
    if bar_index < 16:   return 89, 56    # B  — brighter
    if bar_index < 24:   return 86, 58    # A' — fuller
    return 72, 48                          # coda — hushed


def melody_events():
    ev = []
    t = 0
    for i, (_, mel_bar) in enumerate(SCORE):
        mel_vel, _ = section_vel(i)
        first = True
        for n, eighths in M[mel_bar]:
            dur = eighths * EIGHTH
            if n is not None:
                vel = mel_vel + (4 if first else 0)
                vel = 66 if mel_bar == 28 else vel    # the final note, soft
                note(ev, t, n, dur, vel, 0)
            t += dur
            first = False
    return ev


def accomp_events():
    ev = []
    for i, (chord, _) in enumerate(SCORE):
        base = i * BAR
        bass, tones = VOICINGS[chord]
        arp = [bass] + tones
        _, lh_vel = section_vel(i)

        cc(ev, base, 64, 127)                          # pedal down
        cc(ev, base + BAR - 15, 64, 0)                 # ...and up just before the next bar

        if i == len(SCORE) - 1:                        # final bar: roll the chord and hold
            for j, n in enumerate(arp):
                note(ev, base + j * 30, n, BAR - j * 30, lh_vel + 4, 0)
            continue

        for step, idx in enumerate(LH_PATTERN):
            vel = lh_vel + (8 if idx == 0 else 0)
            note(ev, base + step * EIGHTH, arp[idx], EIGHTH, vel, 0)
    return ev


def write_nocturne(path):
    mid = MidiFile(ticks_per_beat=TPB)
    mid.tracks.append(build_track(melody_events(), "Piano RH", PIANO_PROGRAM, meta=True))
    mid.tracks.append(build_track(accomp_events(), "Piano LH"))
    mid.save(path)


def build_sheet(basename="nocturne"):
    """Engrave the score from the same note data, via the shared to_sheet library."""
    from to_sheet import Sheet
    sh = Sheet("Nocturne in E minor", subtitle="Lamplight",
               composer="for Ehud · generated",
               time_signature="6/8", key_sig="e", tempo=("Andante espressivo", TEMPO_BPM))
    rh, lh = sh.part("treble"), sh.part("bass")

    section_dyn = {0: "mp", 8: "mf", 16: "f", 24: "p"}
    last = len(SCORE) - 1
    for i, (chord_name, mel_bar) in enumerate(SCORE):
        # right hand — the melody
        if i in section_dyn:
            rh.dyn(section_dyn[i])
        for n, eighths in M[mel_bar]:
            ql = eighths * 0.5
            if n is None:
                rh.rest(ql)
            else:
                rh.note(n, ql, fermata=(i == last))
        # left hand — the arpeggio (or a rolled chord in the final bar)
        bass, tones = VOICINGS[chord_name]
        arp = [bass] + tones
        if i == last:
            lh.chord(arp, 3.0, fermata=True)
        else:
            for idx in LH_PATTERN:
                lh.note(arp[idx], 0.5)
    return sh.render(basename)


if __name__ == "__main__":
    OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "nocturne.mid")
    write_nocturne(out)
    print(f"wrote {out} — Nocturne in E minor, 'Lamplight'")
    print(f"  {len(SCORE)} bars of 6/8 at {TEMPO_BPM} BPM (quarter); ternary A-B-A' + coda")
    print(f"  A:    {' '.join(c for c, _ in SCORE[:8])}")
    print(f"  B:    {' '.join(c for c, _ in SCORE[8:16])}")
    print(f"  A':   {' '.join(c for c, _ in SCORE[16:24])}")
    print(f"  coda: {' '.join(c for c, _ in SCORE[24:])}")
    print("tracks: 1) Piano RH  2) Piano LH (sustain pedal included) — both channel 0")
    print("drag into GarageBand and assign a single Grand Piano to both tracks.")

    if "--sheet" in sys.argv:
        build_sheet()
        print("engraved nocturne.musicxml + nocturne.pdf (open the PDF to print)")
