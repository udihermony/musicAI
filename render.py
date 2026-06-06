"""Generic MIDI renderer. Reads any data/*.yaml and dispatches by track type.

    .venv/bin/python render.py jazz_blues        # writes output/jazz_blues.mid
    .venv/bin/python render.py                   # lists available pieces
    .venv/bin/python render.py --all             # renders every piece

Pieces with custom logic (nocturne, jazz_electronic) have their own script in
pieces/ — run those directly. Everything else goes through here.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.music import load, write_midi, out_path, TRACK_BUILDERS, DATA_DIR


def _n_bars(d, loops):
    """Infer total bar count from the piece's data."""
    tracks = d.get("tracks", [])
    by_type = {td["type"]: td for td in tracks}

    # Walking bass is always one list entry per bar — most reliable.
    if "walking_bass" in by_type:
        return loops * len(by_type["walking_bass"].get("bars", []))

    # Block chords: sum actual beats (chords may have non-uniform duration).
    if "block_chords" in by_type:
        td = by_type["block_chords"]
        default = td.get("beats_per_chord", d.get("beats_per_chord", 4))
        total_beats = sum(c.get("beats", default)
                          for c in td.get("progression", []))
        ts = d.get("time_signature", [4, 4])
        beats_per_bar = ts[0] * (4 / ts[1])
        return loops * int(round(total_beats / beats_per_bar))

    # Sequential melody: derive from total duration.
    if "sequential_melody" in by_type:
        td     = by_type["sequential_melody"]
        total  = sum(e[1] for e in td.get("notes", []))
        ts     = d.get("time_signature", [4, 4])
        bar_ql = ts[0] * (4 / ts[1])
        return max(1, int(round(total / bar_ql)))

    # Scored melody / arpeggio_lh: bar count = length of the score list.
    score = d.get("score", [])
    if score:
        return len(score)

    return loops


def render(name):
    d     = load(name)
    loops = d.get("loops", 1)
    n_bars = _n_bars(d, loops)

    midi_tracks = []
    for i, td in enumerate(d.get("tracks", [])):
        kind    = td["type"]
        builder = TRACK_BUILDERS.get(kind)
        if builder is None:
            raise ValueError(f"Unknown track type {kind!r} in {name}.yaml")

        kwargs = {"first": (i == 0)}
        if kind == "drum_grid":
            kwargs["n_bars"] = n_bars
        else:
            kwargs["loops"] = loops

        midi_tracks.append(builder(td, d, **kwargs))

    path = out_path(f"{name}.mid")
    write_midi(path, midi_tracks)
    return d, path, n_bars


def _list_pieces():
    custom = {"nocturne", "jazz_electronic"}
    return sorted(
        f[:-5] for f in os.listdir(DATA_DIR)
        if f.endswith(".yaml") and f[:-5] not in custom
    )


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        pieces = _list_pieces()
        print("Usage: render.py <piece>  |  render.py --all")
        print(f"Pieces: {', '.join(pieces)}")
        sys.exit(0)

    targets = _list_pieces() if "--all" in args else args

    for name in targets:
        try:
            d, path, n_bars = render(name)
            tracks = d.get("tracks", [])
            tnames = "  ".join(f"{i+1}) {t['name']}" for i, t in enumerate(tracks))
            loops  = d.get("loops", 1)
            print(f"wrote {os.path.basename(path)} — {d.get('title', name)}"
                  f"  [{n_bars} bars, {d.get('tempo')} BPM"
                  + (f", ×{loops} loops" if loops > 1 else "") + "]")
            if tnames:
                print(f"  tracks: {tnames}")
        except Exception as e:
            print(f"ERROR {name}: {e}", file=sys.stderr)
