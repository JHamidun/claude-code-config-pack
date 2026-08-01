"""Shim — delegates to skill: ~/.claude/skills/maps-places/scripts/places_search.py"""
import os, sys, runpy
script = os.path.expanduser("~/.claude/skills/maps-places/scripts/places_search.py")
sys.argv[0] = script
runpy.run_path(script, run_name="__main__")
