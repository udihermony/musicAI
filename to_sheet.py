"""Shared notation engraver: turn musical source data into sheet music.

Two ways to use it:

1. Builder API (high quality — engraves from the *source*, the way the pieces
   store their notes, so rhythms and accidentals come out clean):

       from to_sheet import Sheet
       sh = Sheet("Nocturne in E minor", subtitle="Lamplight",
                  time_signature="6/8", key_sig="e", tempo=("Andante", 76))
       rh = sh.part("treble"); lh = sh.part("bass")
       rh.dyn("mp"); rh.note(71, 1.5); rh.note(67, 0.5); ...
       sh.render("nocturne")            # -> nocturne.musicxml + nocturne.pdf

   Durations are quarterLengths (quarter = 1.0, eighth = 0.5, dotted-quarter 1.5).

2. From a finished MIDI file (quick, lossy — music21 quantizes and guesses
   spelling; fine for a rough look, not for clean classical engraving):

       python to_sheet.py jazz_electronic.mid

Rendering to PDF/PNG uses MuseScore's headless CLI if it's installed (set the
MSCORE env var to override the path); MusicXML is always written.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.music import note_to_midi, notes_to_midi, PROJ_DIR

from music21 import (stream, note, chord, meter, key, tempo, clef, layout,
                     metadata, dynamics, expressions, converter)

_SHARP = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
          6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}
_FLAT = {0: "C", 1: "D-", 2: "D", 3: "E-", 4: "E", 5: "F",
         6: "G-", 7: "G", 8: "A-", 9: "A", 10: "B-", 11: "B"}

_MSCORE_CANDIDATES = [
    os.environ.get("MSCORE", ""),
    "/Applications/MuseScore 4.app/Contents/MacOS/mscore",
    "/Applications/MuseScore 3.app/Contents/MacOS/mscore",
    "mscore", "musescore",
]


def _mscore():
    for c in _MSCORE_CANDIDATES:
        if c and (os.path.exists(c) or _on_path(c)):
            return c
    return None


def _on_path(name):
    return any(os.access(os.path.join(p, name), os.X_OK)
               for p in os.environ.get("PATH", "").split(os.pathsep))


def pitch_name(midi, prefer="sharp"):
    table = _FLAT if prefer == "flat" else _SHARP
    return f"{table[midi % 12]}{midi // 12 - 1}"


class Voice:
    """One staff. Append notes/rests/chords/dynamics left to right."""

    def __init__(self, which_clef, prefer):
        self.s = stream.Part()
        self.s.insert(0, {"treble": clef.TrebleClef(),
                          "bass": clef.BassClef()}[which_clef])
        self._prefer = prefer

    def dyn(self, mark):
        self.s.append(dynamics.Dynamic(mark))
        return self

    def note(self, midi, ql, *, dyn=None, fermata=False):
        if dyn:
            self.dyn(dyn)
        n = note.Note(pitch_name(midi, self._prefer), quarterLength=ql)
        if fermata:
            n.expressions.append(expressions.Fermata())
        self.s.append(n)
        return self

    def rest(self, ql):
        self.s.append(note.Rest(quarterLength=ql))
        return self

    def chord(self, midis, ql, *, fermata=False):
        c = chord.Chord([pitch_name(m, self._prefer) for m in midis], quarterLength=ql)
        if fermata:
            c.expressions.append(expressions.Fermata())
        self.s.append(c)
        return self


class Sheet:
    def __init__(self, title, subtitle=None, composer=None,
                 time_signature="4/4", key_sig="C", tempo=None):
        self.title, self.subtitle, self.composer = title, subtitle, composer
        self.time_signature, self.key_name = time_signature, key_sig
        self.tempo = tempo
        self._prefer = "flat" if key.Key(key_sig).sharps < 0 else "sharp"
        self.voices = []

    def part(self, which_clef="treble"):
        v = Voice(which_clef, self._prefer)
        self.voices.append(v)
        return v

    def _decorate(self, part, with_tempo):
        part.insert(0, meter.TimeSignature(self.time_signature))
        part.insert(0, key.Key(self.key_name))
        if with_tempo and self.tempo is not None:
            if isinstance(self.tempo, (tuple, list)):
                text, bpm = self.tempo
                part.insert(0, tempo.MetronomeMark(text=text, number=bpm))
            else:
                part.insert(0, tempo.MetronomeMark(number=self.tempo))

    def _score(self):
        sc = stream.Score()
        sc.insert(0, metadata.Metadata())
        full = f"{self.title} — “{self.subtitle}”" if self.subtitle else self.title
        sc.metadata.title = self.title
        sc.metadata.movementName = full          # MuseScore shows this as the big title
        if self.composer:
            sc.metadata.composer = self.composer
        parts = [v.s for v in self.voices]
        for i, p in enumerate(parts):
            self._decorate(p, with_tempo=(i == 0))
            sc.insert(0, p)
        if len(parts) > 1:
            sc.insert(0, layout.StaffGroup(parts, symbol="brace", barTogether=True))
        return sc

    def render(self, basename, formats=("musicxml", "pdf")):
        return _render(self._score(), basename, formats)


def from_midi(midi_path, basename=None, formats=("musicxml", "pdf")):
    sc = converter.parse(midi_path)
    base = basename or os.path.splitext(os.path.basename(midi_path))[0]
    return _render(sc, base, formats)


def _target(basename, ext):
    """Bare names land in the repo's output/ dir; a name with a path is honored as-is."""
    if os.path.dirname(basename):
        return os.path.abspath(f"{basename}.{ext}")
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, f"{basename}.{ext}")


def _render(score, basename, formats):
    written = {}
    xml = _target(basename, "musicxml")
    score.write("musicxml", fp=xml)
    written["musicxml"] = xml

    wants_render = [f for f in formats if f in ("pdf", "png")]
    if wants_render:
        ms = _mscore()
        if not ms:
            print("MuseScore CLI not found — wrote MusicXML only "
                  "(set MSCORE or open the .musicxml in a notation app).")
        else:
            for fmt in wants_render:
                out = _target(basename, fmt)
                if _run_mscore(ms, out, written["musicxml"]):
                    written[fmt] = out
                else:
                    print(f"MuseScore could not render {fmt} (it's flaky headless); "
                          f"MusicXML is fine — open it, or rerun to retry.")
    for v in written.values():
        print(f"wrote {v}")
    return written


def _run_mscore(ms, out, xml, attempts=3):
    """MuseScore 4 occasionally SIGABRTs in headless mode; retry a few times."""
    import time
    for i in range(attempts):
        r = subprocess.run([ms, "-o", out, xml],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0 and os.path.exists(out):
            return True
        time.sleep(0.7)
    return False


# ---------------------------------------------------------------------------
# Per-track-type sheet builders (parallel to TRACK_BUILDERS in lib/music.py)
# Each receives a Voice, the track dict, and the global piece dict.
# drum_grid is intentionally absent — drums are not engraved here.
# ---------------------------------------------------------------------------

def _sheet_scored_melody(voice, td, d):
    melodies = {int(k): v for k, v in
                (td.get("melodies") or d.get("melodies", {})).items()}
    score   = td.get("score") or d.get("score", [])
    dyn_map = {int(k): v for k, v in
               (td.get("dynamics") or d.get("dynamics", {})).items()}
    last = len(score) - 1
    for i, (_, mel_ref) in enumerate(score):
        if i in dyn_map:
            voice.dyn(dyn_map[i])
        for pitch, dur_ql in melodies[int(mel_ref)]:
            m = note_to_midi(pitch)
            if m is None:
                voice.rest(dur_ql)
            else:
                voice.note(m, dur_ql, fermata=(i == last))


def _sheet_arpeggio_lh(voice, td, d):
    voicings = td.get("voicings") or d.get("voicings", {})
    score    = td.get("score") or d.get("score", [])
    pattern  = td.get("pattern") or d.get("lh_arpeggio", [])
    ts       = d.get("time_signature", [4, 4])
    bar_ql   = ts[0] * (4 / ts[1])
    step_ql  = bar_ql / max(len(pattern), 1)
    last     = len(score) - 1
    for i, (chord_name, _) in enumerate(score):
        v   = voicings[chord_name]
        arp = [note_to_midi(v["bass"])] + notes_to_midi(v["upper"])
        if i == last:
            voice.chord(arp, bar_ql, fermata=True)
        else:
            for idx in pattern:
                voice.note(arp[idx], step_ql)


def _sheet_sequential_melody(voice, td, d):
    for pitch, dur_ql in td.get("notes", []):
        if pitch is None:
            voice.rest(dur_ql)
        elif isinstance(pitch, list):
            midis = [note_to_midi(p) for p in pitch if note_to_midi(p) is not None]
            voice.chord(midis, dur_ql)
        else:
            m = note_to_midi(pitch)
            if m is not None:
                voice.note(m, dur_ql)


def _sheet_sustained_notes(voice, td, d):
    for pitch, dur_ql in td.get("notes", []):
        voice.note(note_to_midi(pitch), dur_ql)


def _sheet_block_chords(voice, td, d):
    default = td.get("beats_per_chord", d.get("beats_per_chord", 4))
    for c in td.get("progression", []):
        voice.chord(notes_to_midi(c["notes"]), float(c.get("beats", default)))


def _sheet_walking_bass(voice, td, d):
    for bar in td.get("bars", []):
        for pitch in bar:
            voice.note(note_to_midi(pitch), 1.0)


_SHEET_BUILDERS = {
    "scored_melody":     _sheet_scored_melody,
    "arpeggio_lh":       _sheet_arpeggio_lh,
    "sequential_melody": _sheet_sequential_melody,
    "sustained_notes":   _sheet_sustained_notes,
    "block_chords":      _sheet_block_chords,
    "walking_bass":      _sheet_walking_bass,
    # drum_grid: skip — percussion not engraved
}


def build_sheet_from_yaml(name, d=None):
    """Build and render sheet music from a piece's YAML data.

    name: piece name (used for the output file basename)
    d:    already-loaded data dict; if None, loads from data/<name>.yaml

    YAML fields used:
      title, subtitle, composer  — score header
      key:           e.g. 'e', 'C', 'Bb'  (default 'C')
      tempo_marking: text label (e.g. 'Andante espressivo')
      tempo:         BPM number
      time_signature: [num, den]
      tracks[].clef: 'treble' or 'bass' (default 'treble')
    """
    if d is None:
        from lib.music import load
        d = load(name)

    ts = d.get("time_signature", [4, 4])
    tempo_val = (d["tempo_marking"], d.get("tempo", 120)) \
                if "tempo_marking" in d else d.get("tempo")

    sh = Sheet(
        d["title"],
        subtitle=d.get("subtitle"),
        composer=d.get("composer"),
        time_signature=f"{ts[0]}/{ts[1]}",
        key_sig=d.get("key", "C"),
        tempo=tempo_val,
    )

    for td in d.get("tracks", []):
        kind    = td.get("type", "")
        builder = _SHEET_BUILDERS.get(kind)
        if builder is None:
            continue                       # drum_grid and unknowns are skipped
        voice = sh.part(td.get("clef", "treble"))
        builder(voice, td, d)

    return sh.render(name)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Engrave a MIDI file to MusicXML/PDF.")
    ap.add_argument("midifile", help="path to a .mid file")
    ap.add_argument("-o", "--out", help="output basename (default: the MIDI's name)")
    ap.add_argument("--no-pdf", action="store_true", help="MusicXML only")
    args = ap.parse_args()
    fmts = ("musicxml",) if args.no_pdf else ("musicxml", "pdf")
    from_midi(args.midifile, basename=args.out, formats=fmts)
