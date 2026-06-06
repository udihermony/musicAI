from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

from jazz_progression import (
    PROGRESSION,
    TEMPO_BPM,
    VELOCITY,
    BEATS_PER_CHORD,
    TICKS_PER_BEAT,
)

DRUM_CHANNEL = 9  # GM channel 10
RIDE = 51
PEDAL_HH = 44
HIT_LEN = 50  # ticks — short percussion blip


def build_chord_track(progression, beats_per_chord: int) -> MidiTrack:
    track = MidiTrack()
    track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
    track.append(MetaMessage("track_name", name="Jazz Chords"))
    duration = TICKS_PER_BEAT * beats_per_chord
    for _, chord in progression:
        for note in chord:
            track.append(Message("note_on", note=note, velocity=VELOCITY, time=0, channel=0))
        for i, note in enumerate(chord):
            track.append(Message("note_off", note=note, velocity=0, time=duration if i == 0 else 0, channel=0))
    return track


def build_drum_track(num_bars: int) -> MidiTrack:
    """Swing ride on every beat + swung 'and' on 2 & 4, pedal hi-hat on 2 & 4."""
    swung = (TICKS_PER_BEAT * 2) // 3  # triplet 'and'
    events = []  # (abs_tick, kind, note, velocity)

    for bar in range(num_bars):
        for beat in range(4):
            t = bar * 4 * TICKS_PER_BEAT + beat * TICKS_PER_BEAT
            vel = 75 if beat in (1, 3) else 60  # accent 2 and 4
            events.append((t, "on", RIDE, vel))
            events.append((t + HIT_LEN, "off", RIDE, 0))
            if beat in (1, 3):
                events.append((t, "on", PEDAL_HH, 55))
                events.append((t + HIT_LEN, "off", PEDAL_HH, 0))
                events.append((t + swung, "on", RIDE, 65))
                events.append((t + swung + HIT_LEN, "off", RIDE, 0))

    events.sort(key=lambda e: (e[0], 0 if e[1] == "on" else 1))

    track = MidiTrack()
    track.append(MetaMessage("track_name", name="Jazz Drums"))
    prev = 0
    for abs_t, kind, note, vel in events:
        delta = abs_t - prev
        msg_type = "note_on" if kind == "on" else "note_off"
        track.append(Message(msg_type, note=note, velocity=vel, time=delta, channel=DRUM_CHANNEL))
        prev = abs_t
    return track


def write_full_arrangement(path: str) -> None:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    mid.tracks.append(build_chord_track(PROGRESSION, BEATS_PER_CHORD))
    mid.tracks.append(build_drum_track(num_bars=len(PROGRESSION)))
    mid.save(path)


if __name__ == "__main__":
    out = "jazz_with_drums.mid"
    write_full_arrangement(out)
    print(f"wrote {out} — {len(PROGRESSION)} chords + swing drums")
    print("drag into GarageBand → 2 tracks. Assign a piano to track 1, a drum kit to track 2.")
