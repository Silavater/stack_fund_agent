"""Enable ``python -m stackfund`` (the container ENTRYPOINT)."""

from __future__ import annotations

from stackfund.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
