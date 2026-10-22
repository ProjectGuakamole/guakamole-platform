"""CLI restringida para migraciones controladas."""

from app.core.migrations import main

if __name__ == "__main__":
    raise SystemExit(main())
