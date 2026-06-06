from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

# ---------------------------------------------------------------------------
# Jazz-electronic, a bit experimental. 16-bar A/B form.
#
#   A (bars 1-8): dark A-minor modal loop, syncopated comp + active bass.
#   B (bars 9-16): the harmonic development. A low A drops to a *drone* and
#       maj7#11 shapes plane over it in parallel motion, arcing out to the
#       crunch and back (Bb-C-Db-C-Bb-Ab / A), then the bass lifts off the
#       pedal for a chromatic Cm9 -> Bb13 tritone-sub turnaround that slides
#       home (Bb -> A) instead of the A-section's V7.
#
# The hook through both: the arp runs a 3-against-4 polyrhythm (a note every
# dotted-eighth) that phases against the 4/4 grid and drifts across the bars,
# so nothing repeats quite where your ear expects.
# ---------------------------------------------------------------------------

TPB = 480
BAR = 4 * TPB          # 1920 — one 4/4 bar
S = TPB // 4           # 120  — one sixteenth
DOTTED_8TH = 3 * S     # 360  — the arp pulse (3-against-4)
SWING = 50             # ticks the offbeat hats get pushed
TEMPO_BPM = 84

CH_KEYS, CH_BASS, CH_ARP, CH_DRUM = 0, 1, 2, 9

# GM programs (matter if you route to a synth; GarageBand ignores them but
# they're a hint: pick a Rhodes, a synth bass, and a saw lead).
PROG_KEYS, PROG_BASS, PROG_ARP = 4, 38, 81

# Per bar: name, Rhodes voicing (mid register), bass root, bass style.
# style "figure" = the syncopated synth-bass riff; "drone" = sustained pedal +
# a sustained pad-style Rhodes (lets the planing chords ring). Notes are MIDI
# numbers; the arp pool is derived from the voicing.
#
# A section: i - iv - bII - bVI - V7b9 (dark, everything resolves inward).
A_SECTION = [
    ("Am9",        [60, 64, 67, 71], 33, "figure"),  # C4 E4 G4 B4   / A1   3 5 b7 9
    ("Am9",        [60, 64, 67, 71], 33, "figure"),
    ("Dm9",        [65, 69, 72, 76], 38, "figure"),  # F4 A4 C5 E5   / D2   b3 5 b7 9
    ("Dm9",        [65, 69, 72, 76], 38, "figure"),
    ("Bbmaj7#11",  [62, 65, 69, 76], 34, "figure"),  # D4 F4 A4 E5   / Bb1  3 5 7 #11
    ("Fmaj9",      [57, 60, 64, 67], 29, "figure"),  # A3 C4 E4 G4   / F1   3 5 7 9
    ("E7b9",       [68, 71, 74, 77], 28, "figure"),  # G#4 B4 D5 F5  / E1   3 5 b7 b9
    ("E7b9",       [68, 71, 74, 77], 28, "figure"),
]

# B section: maj7#11 shape [R+4, R+7, R+11, R+18] planed over an A drone (33),
# arcing Bb-C-Db-C-Bb-Ab, then off the pedal for the Cm9 -> Bb13 tritone sub.
B_SECTION = [
    ("Bbmaj7#11/A", [62, 65, 69, 76], 33, "drone"),  # D4  F4  A4  E5   over A pedal
    ("Cmaj7#11/A",  [64, 67, 71, 78], 33, "drone"),  # E4  G4  B4  F#5  -> bright (Am13)
    ("Dbmaj7#11/A", [65, 68, 72, 79], 33, "drone"),  # F4  G#4 C5  G5   -> tension
    ("Cmaj7#11/A",  [64, 67, 71, 78], 33, "drone"),  # release back
    ("Bbmaj7#11/A", [62, 65, 69, 76], 33, "drone"),
    ("Abmaj7#11/A", [60, 63, 67, 74], 33, "drone"),  # C4  Eb4 G4  D5   -> crunch (Eb vs A)
    ("Cm9",         [63, 67, 70, 74], 36, "figure"), # Eb4 G4  Bb4 D5   / C2  off the pedal
    ("Bb13",        [62, 68, 72, 79], 34, "figure"), # D4  Ab4 C5  G5   / Bb1 tritone sub -> A
]

CHORDS = A_SECTION + B_SECTION
N_BARS = len(CHORDS)

# Two-hit syncopated Rhodes comp per bar: (start, duration). Hit on beat 1,
# pushed again on the "and of 3".
KEYS_COMP = [(0, 1200), (1200, 720)]

# Syncopated synth-bass figure: (start_16th, len_16ths, octave_offset).
BASS_FIGURE = [(0, 3, 0), (3, 1, 0), (6, 2, 12), (10, 2, 0), (12, 3, 12)]


def arp_pool(voicing):
    """Chord-tone ladder for the arp: the voicing plus its bottom two an octave up."""
    return voicing + [voicing[0] + 12, voicing[1] + 12]


def add(events, t, note, dur, vel, ch):
    events.append((t, 1, note, vel, ch))            # note_on   (sort key 1)
    events.append((t + dur, 0, note, 0, ch))        # note_off  (sort key 0, fires first on ties)


def build_track(events, name, program=None, channel=0, meta_first=False):
    track = MidiTrack()
    if meta_first:
        track.append(MetaMessage("set_tempo", tempo=bpm2tempo(TEMPO_BPM)))
        track.append(MetaMessage("time_signature", numerator=4, denominator=4))
    track.append(MetaMessage("track_name", name=name))
    if program is not None:
        track.append(Message("program_change", program=program, channel=channel, time=0))

    events = sorted(events, key=lambda e: (e[0], e[1]))
    prev = 0
    for abs_t, kind, note, vel, ch in events:
        delta = abs_t - prev
        msg = "note_on" if kind == 1 else "note_off"
        track.append(Message(msg, note=note, velocity=vel, time=delta, channel=ch))
        prev = abs_t
    return track


def keys_events():
    ev = []
    for bar, (_, voicing, _, style) in enumerate(CHORDS):
        base = bar * BAR
        hits = [(0, BAR)] if style == "drone" else KEYS_COMP   # drone bars ring as a pad
        for start, dur in hits:
            vel = 70 if style == "drone" else (78 if start == 0 else 68)
            for n in voicing:
                add(ev, base + start, n, dur, vel, CH_KEYS)
    return ev


def bass_events():
    ev = []
    for bar, (_, _, root, style) in enumerate(CHORDS):
        base = bar * BAR
        if style == "drone":
            add(ev, base, root, BAR, 88, CH_BASS)              # sustained pedal
            continue
        for pos, length, octv in BASS_FIGURE:
            vel = 100 if pos == 0 else 84
            add(ev, base + pos * S, root + octv, length * S, vel, CH_BASS)
    return ev


def arp_events():
    """Continuous dotted-eighth stream cycling each bar's chord tones — the 3-against-4."""
    ev = []
    total = N_BARS * BAR
    step = 0
    t = 0
    while t < total:
        bar = t // BAR
        pool = arp_pool(CHORDS[bar][1])
        note = pool[step % len(pool)]
        dur = min(220, total - t)               # plucky, leaves an electronic gap
        vel = 90 if t % BAR == 0 else 74        # accent the downbeat hit
        add(ev, t, note, dur, vel, CH_ARP)
        step += 1
        t += DOTTED_8TH
    return ev


def drum_events():
    KICK, SNARE, CLAP, HC, HO, SHK = 36, 38, 39, 42, 46, 70
    ev = []
    for bar in range(N_BARS):
        base = bar * BAR
        section_end = (bar + 1) % 8 == 0                      # fill into B and into the loop

        for p in (0, 6, 10):                                  # syncopated kick
            add(ev, base + p * S, KICK, S, 110 if p == 0 else 96, CH_DRUM)

        for p in (4, 12):                                     # backbeat snare + clap layer
            add(ev, base + p * S, SNARE, S, 104, CH_DRUM)
            add(ev, base + p * S, CLAP, S, 82, CH_DRUM)
        add(ev, base + 7 * S, SNARE, S, 44, CH_DRUM)          # ghost

        for p in range(0, 16, 2):                             # hats on the 8ths, swung
            if p == 14:
                add(ev, base + p * S + SWING, HO, S, 86, CH_DRUM)   # open hat push into next bar
                continue
            offbeat = (p // 2) % 2 == 1
            t = base + p * S + (SWING if offbeat else 0)
            add(ev, t, HC, S, 64 if offbeat else 82, CH_DRUM)

        for p in range(0, 16):                                # shaker texture (16ths)
            add(ev, base + p * S, SHK, S, 34 if p % 2 == 0 else 26, CH_DRUM)

        if section_end:                                       # snare fill into the next section
            for i, p in enumerate(range(10, 16)):
                add(ev, base + p * S, SNARE, S, 60 + i * 9, CH_DRUM)

    return ev


def write_song(path):
    mid = MidiFile(ticks_per_beat=TPB)
    mid.tracks.append(build_track(keys_events(), "Rhodes", PROG_KEYS, CH_KEYS, meta_first=True))
    mid.tracks.append(build_track(bass_events(), "Synth Bass", PROG_BASS, CH_BASS))
    mid.tracks.append(build_track(arp_events(), "Poly Arp", PROG_ARP, CH_ARP))
    mid.tracks.append(build_track(drum_events(), "Drums", channel=CH_DRUM))
    mid.save(path)


if __name__ == "__main__":
    out = "jazz_electronic.mid"
    write_song(out)
    arp_notes = len(arp_events()) // 2
    names = [name for name, _, _, _ in CHORDS]
    print(f"wrote {out} — {N_BARS} bars of 4/4 at {TEMPO_BPM} BPM (A/B form)")
    print(f"  A: {' '.join(names[:8])}")
    print(f"  B: {' '.join(names[8:])}")
    print(f"arp: {arp_notes} dotted-8th notes (3-against-4 polyrhythm, phases across both sections)")
    print("tracks: 1) Rhodes  2) Synth Bass  3) Poly Arp  4) Drums (GM ch10)")
    print("drag into GarageBand — Rhodes/EP on 1, synth bass on 2, a bright saw/pluck on 3, kit on 4.")
