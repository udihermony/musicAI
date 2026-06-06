from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

from jazz_progression import (
    PROGRESSION,
    TEMPO_BPM,
    VELOCITY,
    BEATS_PER_CHORD,
    TICKS_PER_BEAT,
)
from jazz_with_drums import build_drum_track

LOOPS = 4
BASS_CHANNEL = 1
BASS_VELOCITY = 85
NOTE_GAP = 20  # ticks of silence between bass notes for articulation

# Walking bass — one note per beat, last beat is a chromatic approach to the next root.
# Dm7 → G7 (approach via Ab2), G7 → Cmaj7 (approach via Db3), Cmaj7 → Dm7 loop (approach via Eb2).
WALKING_BASS = [
    [38, 41, 45, 44],  # Dm7:   D2  F2  A2  Ab2
    [43, 47, 50, 49],  # G7:    G2  B2  D3  Db3
    [48, 43, 40, 39],  # Cmaj7: C3  G2  E2  Eb2
]


def build_chord_track_looped(progression, beats_per_chord: int, loops: int) -> MidiTrack:
    track = MidiTrack()
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
    track.append(MetaMessage("track_name", name="Jazz Chords"))
    duration = TICKS_PER_BEAT * beats_per_chord
    for _ in range(loops):
        for _, chord in progression:
            for note in chord:
                track.append(Message("note_on", note=note, velocity=VELOCITY, time=0, channel=0))
            for i, note in enumerate(chord):
                track.append(Message("note_off", note=note, velocity=0, time=duration if i == 0 else 0, channel=0))
    return track


def build_bass_track_looped(walking_bass, loops: int) -> MidiTrack:
    track = MidiTrack()
    track.append(MetaMessage("track_name", name="Walking Bass"))
    note_dur = TICKS_PER_BEAT - NOTE_GAP
    first = True
    for _ in range(loops):
        for bar in walking_bass:
            for note in bar:
                on_time = 0 if first else NOTE_GAP
                track.append(Message("note_on", note=note, velocity=BASS_VELOCITY, time=on_time, channel=BASS_CHANNEL))
                track.append(Message("note_off", note=note, velocity=0, time=note_dur, channel=BASS_CHANNEL))
                first = False
    return track


def write_full(path: str, loops: int = LOOPS) -> None:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    mid.tracks.append(build_chord_track_looped(PROGRESSION, BEATS_PER_CHORD, loops))
    mid.tracks.append(build_bass_track_looped(WALKING_BASS, loops))
    mid.tracks.append(build_drum_track(num_bars=loops * len(PROGRESSION)))
    mid.save(path)


if __name__ == "__main__":
    import os
    OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "jazz_full.mid")
    write_full(out, loops=LOOPS)
    total_bars = LOOPS * len(PROGRESSION)
    print(f"wrote {out} — {LOOPS} loops × {len(PROGRESSION)} bars = {total_bars} bars")
    print("tracks: 1) Jazz Chords  2) Walking Bass  3) Jazz Drums")
    print("drag into GarageBand — assign piano / upright bass / drum kit.")
