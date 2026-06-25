"""Shared pytest fixtures for the Lost Friend API test suite."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token

# Import app AFTER dependency overrides are set up in fixture
from main import app


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession with chainable execute() and .get()."""
    session = AsyncMock(spec=AsyncSession)

    # execute() returns a mock Result
    execute_result = MagicMock()
    session.execute.return_value = execute_result

    # scalar_one_or_none() returns None by default
    execute_result.scalar_one_or_none.return_value = None

    # scalars().all() returns empty list
    scalars_mock = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    scalars_mock.all.return_value = []

    # .all() on result directly
    execute_result.all.return_value = []

    # db.get() — separate from execute
    session.get = AsyncMock(return_value=None)

    # db.add(), db.commit(), etc.
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    return session


@pytest.fixture
def test_client(mock_db_session):
    """TestClient with overridden get_db dependency."""
    app.dependency_overrides = {}

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """JWT token for a regular user (id=1)."""
    token = create_access_token({"sub": "1"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_authority():
    """JWT token for an authority user (id=1, tipo=autoridad)."""
    token = create_access_token({"sub": "1", "tipo": "autoridad"})
    return {"Authorization": f"Bearer {token}"}


class _AlertRow:
    """Simula SQLAlchemy Row: row[0] devuelve self, row tiene named attrs.

    Usado en tests de alerta_service.listar_alertas_activas_service
    que accede a row[0] para el objeto Alerta y row.nombre_attr para labels.
    """

    def __getitem__(self, idx: int) -> object:
        if idx == 0:
            return self
        raise IndexError


@pytest.fixture
def mock_current_user(mock_db_session: AsyncMock) -> MagicMock:
    """Configura mock_db_session.get para devolver un Usuario mockeado.

    Útil para endpoints protegidos por get_current_user / get_current_actor.
    """
    from datetime import datetime, timezone

    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.correo = "test@test.com"
    mock_user.nombre = "Test User"
    mock_user.telefono = None
    mock_user.fcm_token = None
    mock_user.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_user.updated_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    mock_db_session.get.return_value = mock_user
    return mock_user


@pytest.fixture
def mock_current_authority(mock_db_session: AsyncMock) -> MagicMock:
    """Configura mock_db_session.get para devolver una Autoridad mockeada.

    Útil para endpoints protegidos por get_current_actor con token de autoridad.
    """
    mock_authority = MagicMock()
    mock_authority.id = 1
    mock_authority.email = "policia@test.com"
    mock_authority.nombre = "Policía Local"
    mock_authority.codigo_autoridad = "POL-001"
    mock_db_session.get.return_value = mock_authority
    return mock_authority
