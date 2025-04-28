import pytest
from httpx import AsyncClient
from maintest import app

# Configuration du backend asyncio pour pytest-asyncio
@pytest.fixture()
def anyio_backend():
    return 'asyncio'

# Client HTTP FastAPI pour les tests
@pytest.fixture()
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
