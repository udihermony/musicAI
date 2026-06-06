from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

# Time framing: Für Elise is in 3/8. Treat eighth note as the "beat".
TICKS_PER_BEAT = 480       # = one eighth note
SIXTEENTH = 240
EIGHTH = 480
DOTTED_EIGHTH = 720
BAR_TICKS = 3 * EIGHTH     # 1440 — one 3/8 bar

TEMPO_BPM = 140            # eighth-note pulse → roughly quarter ≈ 70

MELODY_CHANNEL = 0
BASS_CHANNEL = 1
MELODY_VELOCITY = 95
BASS_VELOCITY = 70

# (midi_note or None for rest, duration_in_ticks)
# Notes: E5=76 D#5=75 D5=74 C5=72 B4=71 A4=69 G#4=68 E4=64 C4=60
MELODY = [
    # Bar 1 (Am): E5 D#5 E5 D#5 E5 B4
    (76, SIXTEENTH), (75, SIXTEENTH), (76, SIXTEENTH),
    (75, SIXTEENTH), (76, SIXTEENTH), (71, SIXTEENTH),
    # Bar 2 (Am): D5 C5 A4 — rest
    (74, SIXTEENTH), (72, SIXTEENTH), (69, EIGHTH), (None, EIGHTH),
    # Bar 3 (Am): C4 E4 A4 B4 — rising answer
    (60, SIXTEENTH), (64, SIXTEENTH), (69, SIXTEENTH), (71, EIGHTH), (None, SIXTEENTH),
    # Bar 4 (E): E4 G#4 B4 C5 — leading tone, lands on C
    (64, SIXTEENTH), (68, SIXTEENTH), (71, SIXTEENTH), (72, EIGHTH), (None, SIXTEENTH),
    # Bar 5 (Am): repeat of bar 1
    (76, SIXTEENTH), (75, SIXTEENTH), (76, SIXTEENTH),
    (75, SIXTEENTH), (76, SIXTEENTH), (71, SIXTEENTH),
    # Bar 6 (Am): repeat of bar 2
    (74, SIXTEENTH), (72, SIXTEENTH), (69, EIGHTH), (None, EIGHTH),
    # Bar 7 (Am): same rising answer
    (60, SIXTEENTH), (64, SIXTEENTH), (69, SIXTEENTH), (71, EIGHTH), (None, SIXTEENTH),
    # Bar 8 (E → Am): E4 C5 B4 A4 — cadence home
    (64, SIXTEENTH), (72, SIXTEENTH), (71, SIXTEENTH), (69, DOTTED_EIGHTH),
]

# One sustained low note per bar — Am where the motif sits, E under the leading-tone bar.
# A2=45, E2=40
BASS_LINE = [
    (45, BAR_TICKS),  # bar 1  Am
    (45, BAR_TICKS),  # bar 2  Am
    (45, BAR_TICKS),  # bar 3  Am
    (40, BAR_TICKS),  # bar 4  E (G# in melody = leading tone)
    (45, BAR_TICKS),  # bar 5  Am
    (45, BAR_TICKS),  # bar 6  Am
    (45, BAR_TICKS),  # bar 7  Am
    (40, BAR_TICKS),  # bar 8  E → resolves to A on the loop
]


def build_track(events, channel: int, velocity: int, name: str, with_tempo: bool = False) -> MidiTrack:
    track = MidiTrack()
    if with_tempo:
        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
    track.append(MetaMessage("track_name", name=name))

    pending_rest = 0
    for note, dur in events:
        if note is None:
            pending_rest += dur
            continue
        track.append(Message("note_on", note=note, velocity=velocity, time=pending_rest, channel=channel))
        track.append(Message("note_off", note=note, velocity=0, time=dur, channel=channel))
        pending_rest = 0
    return track


def write_fur_elise(path: str) -> None:
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    mid.tracks.append(build_track(MELODY, MELODY_CHANNEL, MELODY_VELOCITY, "Melody", with_tempo=True))
    mid.tracks.append(build_track(BASS_LINE, BASS_CHANNEL, BASS_VELOCITY, "Bass", with_tempo=False))
    mid.save(path)


if __name__ == "__main__":
    import os
    OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, "fur_elise.mid")
    write_fur_elise(out)
    melody_bars = sum(d for _, d in MELODY) / BAR_TICKS
    bass_bars = sum(d for _, d in BASS_LINE) / BAR_TICKS
    print(f"wrote {out} — melody: {melody_bars:.1f} bars, bass: {bass_bars:.1f} bars")
    print("tracks: 1) Melody  2) Bass")
    print("drag into GarageBand — assign piano to melody, upright bass or cello to bass.")
