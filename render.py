"""Render any project to MIDI (and optionally sheet music).

    .venv/bin/python render.py nocturne              # one project
    .venv/bin/python render.py --all                 # every project
    .venv/bin/python render.py --sheet nocturne      # MIDI + PDF score
    .venv/bin/python render.py                       # list available projects

Each project lives in projects/<name>/ and must have data.yaml.
If the project also has custom.py, its render(d) function is called instead
of the generic YAML dispatcher — used for algorithmically generated tracks.
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.music import load, write_midi, out_path, TRACK_BUILDERS, PROJ_DIR


PROJECTS_DIR = PROJ_DIR


def _n_bars(d, loops):
    """Infer total bar count from the piece's data."""
    # Explicit declaration always wins.
    if "n_bars" in d:
        return d["n_bars"]

    tracks  = d.get("tracks", [])
    by_type = {td["type"]: td for td in tracks}

    if "walking_bass" in by_type:
        return loops * len(by_type["walking_bass"].get("bars", []))

    if "block_chords" in by_type:
        td      = by_type["block_chords"]
        default = td.get("beats_per_chord", d.get("beats_per_chord", 4))
        total   = sum(c.get("beats", default) for c in td.get("progression", []))
        ts      = d.get("time_signature", [4, 4])
        return loops * int(round(total / (ts[0] * (4 / ts[1]))))

    if "sequential_melody" in by_type:
        td     = by_type["sequential_melody"]
        total  = sum(e[1] for e in td.get("notes", []))
        ts     = d.get("time_signature", [4, 4])
        bar_ql = ts[0] * (4 / ts[1])
        return max(1, int(round(total / bar_ql)))

    score = d.get("score", [])
    if score:
        return len(score)

    return loops * len(d.get("chords", []))


def _load_custom(name):
    """Import projects/<name>/custom.py and return its render(d) function, or None."""
    path = os.path.join(PROJECTS_DIR, name, "custom.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(f"{name}_custom", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "render", None)


def render(name):
    d      = load(name)
    loops  = d.get("loops", 1)
    n_bars = _n_bars(d, loops)

    custom = _load_custom(name)
    if custom:
        midi_tracks = custom(d)
    else:
        midi_tracks = []
        for i, td in enumerate(d.get("tracks", [])):
            kind    = td["type"]
            builder = TRACK_BUILDERS.get(kind)
            if builder is None:
                raise ValueError(f"Unknown track type {kind!r} in {name}/data.yaml")
            kwargs = {"first": (i == 0)}
            if kind == "drum_grid":
                kwargs["n_bars"] = n_bars
            else:
                kwargs["loops"] = loops
            midi_tracks.append(builder(td, d, **kwargs))

    path = out_path(f"{name}.mid")
    write_midi(path, midi_tracks)
    return d, path, n_bars


def _list_projects():
    return sorted(
        p for p in os.listdir(PROJECTS_DIR)
        if os.path.isdir(os.path.join(PROJECTS_DIR, p))
        and os.path.exists(os.path.join(PROJECTS_DIR, p, "data.yaml"))
    )


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print("Usage: render.py <project>  |  render.py --all  |  render.py --sheet <project>")
        print(f"Projects: {', '.join(_list_projects())}")
        sys.exit(0)

    want_sheet = "--sheet" in args
    targets    = _list_projects() if "--all" in args else [a for a in args if not a.startswith("-")]

    for name in targets:
        try:
            d, path, n_bars = render(name)
            loops  = d.get("loops", 1)
            tracks = d.get("tracks", [])
            has_custom = os.path.exists(os.path.join(PROJECTS_DIR, name, "custom.py"))
            tnames = "  ".join(f"{i+1}) {t['name']}" for i, t in enumerate(tracks)) \
                     or "(custom tracks)"
            print(f"wrote {os.path.basename(path)} — {d.get('title', name)}"
                  f"  [{n_bars} bars, {d.get('tempo')} BPM"
                  + (f", ×{loops} loops" if loops > 1 else "")
                  + (" [custom]" if has_custom else "") + "]")
            print(f"  tracks: {tnames}")
            if want_sheet:
                from to_sheet import build_sheet_from_yaml
                build_sheet_from_yaml(name, d)
        except Exception as e:
            print(f"ERROR {name}: {e}", file=sys.stderr)
            raise
