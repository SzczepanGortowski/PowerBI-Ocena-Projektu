"""Punkt wejścia: python standardy.py --raport "<.pbip | .pbix | folder .Report>" [opcje] (szczegóły: --help)."""
import sys

from standardy_wiz.__main__ import glowna

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(glowna())
