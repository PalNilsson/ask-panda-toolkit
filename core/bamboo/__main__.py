"""Module entry point for `python -m bamboo`.

This dispatches to the CLI.
"""
from bamboo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
