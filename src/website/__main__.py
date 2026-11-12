"""Run a local development server with ``uv run website``."""

import uvicorn


def main() -> None:
    """Serve the app with auto-reload at http://127.0.0.1:8000."""
    uvicorn.run("website.app:create_app", factory=True, host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
