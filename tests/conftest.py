import pytest
from httpx import AsyncClient
from maintest import app

from app.db.database import get_db

@pytest.fixture()
def anyio_backend():
    return 'asyncio'

# Client HTTP FastAPI pour les tests
@pytest.fixture()
async def client():
    # Use default dependency (Postgres service in CI)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
