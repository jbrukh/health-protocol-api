import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base
from app.main import app
from app.database import get_db
from app.auth import verify_api_key

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_API_KEY = "test-api-key"

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Shared session for test
_test_session: AsyncSession = None


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override get_db to use test session."""
    global _test_session
    try:
        yield _test_session
        await _test_session.commit()
    except Exception:
        await _test_session.rollback()
        raise


async def override_verify_api_key() -> str:
    return TEST_API_KEY


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden dependencies."""
    global _test_session

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session for this test
    _test_session = TestSessionLocal()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await _test_session.close()
    _test_session = None
    app.dependency_overrides.clear()

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def api_headers() -> dict:
    """Return headers with test API key."""
    return {"Authorization": f"Bearer {TEST_API_KEY}"}


@pytest.fixture(scope="function")
async def client_no_auth() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client without auth override for testing unauthorized access."""
    global _test_session

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session for this test
    _test_session = TestSessionLocal()

    # Only override get_db, NOT verify_api_key
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    await _test_session.close()
    _test_session = None
    app.dependency_overrides.clear()

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
