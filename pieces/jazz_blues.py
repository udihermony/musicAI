from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

from jazz_progression import TEMPO_BPM, VELOCITY, TICKS_PER_BEAT
from jazz_with_drums import build_drum_track
from jazz_full import build_bass_track_looped, LOOPS

# F jazz blues — 12 bars. Each entry: (label, chord notes, beats).
PROGRESSION_BLUES = [
    ("F7",    [65, 69, 72, 75], 4),  # I7
    ("Bb7",   [58, 62, 65, 68], 4),  # IV7
    ("F7",    [65, 69, 72, 75], 4),  # I7
    ("Cm7",   [60, 63, 67, 70], 2),  # ii of IV
    ("F7",    [65, 69, 72, 75], 2),  # V7 of IV
    ("Bb7",   [58, 62, 65, 68], 4),  # IV7
    ("Bdim7", [59, 62, 65, 68], 4),  # #IV diminished passing
    ("F7",    [65, 69, 72, 75], 4),  # I7
    ("D7",    [62, 66, 69, 72], 4),  # V of ii (secondary dominant)
    ("Gm7",   [55, 58, 62, 65], 4),  # ii
    ("C7",    [60, 64, 67, 70], 4),  # V7
    ("F7",    [65, 69, 72, 75], 4),  # I7
    ("Gm7",   [55, 58, 62, 65], 2),  # turnaround ii
    ("C7",    [60, 64, 67, 70], 2),  # turnaround V
]

# Walking bass — 12 bars × 4 beats. Last beat of each bar approaches the next root chromatically.
WALKING_BASS_BLUES = [
    [41, 45, 48, 47],  # F7:      F2 A2 C3 B2   (→ Bb)
    [46, 50, 53, 52],  # Bb7:     Bb2 D3 F3 E3  (→ F)
    [41, 45, 48, 47],  # F7:      F2 A2 C3 B2   (→ C)
    [48, 51, 41, 47],  # Cm7|F7:  C3 Eb3 | F2 B2 (→ Bb)
    [46, 50, 53, 48],  # Bb7:     Bb2 D3 F3 C3  (→ B)
    [47, 50, 53, 56],  # Bdim7:   B2 D3 F3 Ab3  (→ F)
    [41, 45, 48, 49],  # F7:      F2 A2 C3 C#3  (→ D)
    [50, 54, 57, 56],  # D7:      D3 F#3 A3 Ab3 (→ G)
    [43, 46, 50, 49],  # Gm7:     G2 Bb2 D3 C#3 (→ C)
    [48, 52, 55, 54],  # C7:      C3 E3 G3 F#3  (→ F)
    [41, 45, 48, 44],  # F7:      F2 A2 C3 Ab2  (→ G)
    [43, 46, 48, 40],  # Gm7|C7:  G2 Bb2 | C3 E2 (→ F, loop)
]


def build_chord_track_variable(progression, loops: int) -> MidiTrack:
    track = MidiTrack()
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
    track.append(MetaMessage("track_name", name="Blues Chords"))
    for _ in range(loops):
        for _, chord, beats in progression:
            duration = TICKS_PER_BEAT * beats
            for note in chord:
                track.append(Message("note_on", note=note, velocity=VELOCITY, time=0, channel=0))
            for i, note in enumerate(chord):
                track.append(Message("note_off", note=note, velocity=0, time=duration if i == 0 else 0, channel=0))
    return track


def write_blues(path: str, loops: int = LOOPS) -> None:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    mid.tracks.append(build_chord_track_variable(PROGRESSION_BLUES, loops))
    mid.tracks.append(build_bass_track_looped(WALKING_BASS_BLUES, loops))
    mid.tracks.append(build_drum_track(num_bars=loops * len(WALKING_BASS_BLUES)))
    mid.save(path)


if __name__ == "__main__":
    out = "jazz_blues.mid"
    write_blues(out)
    total_bars = LOOPS * len(WALKING_BASS_BLUES)
    print(f"wrote {out} — F jazz blues, 12 bars × {LOOPS} loops = {total_bars} bars")
    print("tracks: 1) Blues Chords  2) Walking Bass  3) Jazz Drums")
