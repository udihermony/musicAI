from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

TICKS_PER_BEAT = 480
BEATS_PER_CHORD = 4
VELOCITY = 80
TEMPO_BPM = 120

# ii - V - I in C major: Dm7, G7, Cmaj7
PROGRESSION = [
    ("Dm7",   [62, 65, 69, 72]),
    ("G7",    [67, 71, 74, 77]),
    ("Cmaj7", [60, 64, 67, 71]),
]


def write_progression(path: str, progression, beats_per_chord: int = BEATS_PER_CHORD) -> None:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))

    duration = TICKS_PER_BEAT * beats_per_chord

    for _, chord in progression:
        for note in chord:
            track.append(Message("note_on", note=note, velocity=VELOCITY, time=0))
        for i, note in enumerate(chord):
            track.append(Message("note_off", note=note, velocity=0, time=duration if i == 0 else 0))

    mid.save(path)


if __name__ == "__main__":
    import os
    OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "jazz_progression.mid")
    write_progression(out, PROGRESSION)
    print(f"wrote {out} — {len(PROGRESSION)} chords @ {TEMPO_BPM} bpm")
    print("drag this .mid file onto a Software Instrument track in GarageBand")
