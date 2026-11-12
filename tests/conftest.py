"""Shared test fixtures."""

import socket
import threading
import time
from collections.abc import Iterator
from typing import Final

import httpx2
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from website.app import create_app
from website.config import Settings

LIVE_REVISION: Final = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def settings() -> Settings:
    """Settings with no known revision."""
    return Settings(revision=None)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """Application under test."""
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Test client for the application under test."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def live_server() -> Iterator[str]:
    """Run the real application with Uvicorn on a free local port.

    Yields:
        The server's base URL.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    config = uvicorn.Config(
        create_app(Settings(revision=LIVE_REVISION)), log_level="warning", lifespan="off"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while True:
        try:
            if httpx2.get(f"{base_url}/healthz", timeout=1).status_code == 200:
                break
        except httpx2.TransportError:
            pass
        if time.monotonic() > deadline:
            msg = "Live server did not start within 10 seconds"
            raise RuntimeError(msg)
        time.sleep(0.05)

    yield base_url

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def base_url(live_server: str) -> str:
    """Point pytest-playwright's relative URLs at the live server."""
    return live_server
