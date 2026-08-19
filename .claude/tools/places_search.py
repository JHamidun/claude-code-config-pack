"""Shim — delegates to the maps-places skill script (skills/maps-places/scripts/places_search.py)."""
import os
import sys
import runpy


def _find_script():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # Repo/clone layout: <root>/tools/ -> <root>/skills/...
        os.path.join(here, "..", "skills", "maps-places", "scripts", "places_search.py"),
        # Installed layout
        os.path.expanduser("~/.claude/skills/maps-places/scripts/places_search.py"),
    ]
    for c in candidates:
        c = os.path.normpath(c)
        if os.path.isfile(c):
            return c
    return None


def main():
    script = _find_script()
    if script is None:
        sys.exit(
            "ERROR: maps-places skill script not found.\n"
            "Expected at skills/maps-places/scripts/places_search.py (next to tools/)\n"
            "or ~/.claude/skills/maps-places/scripts/places_search.py — install the skill first."
        )
    sys.argv[0] = script
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
