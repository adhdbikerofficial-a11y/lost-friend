"""Tests for service-layer functions — mocked DB, patched dependencies."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.alerta import AlertaRequest
from app.schemas.mascota import MascotaRequest
from app.services.alerta_service import AlertaError, cancelar_alerta, crear_alerta, listar_alertas_activas_service, resolver_alerta
from app.services.auth_service import AuthError, login, login_autoridad, register
from app.services.mascota_service import (
    MascotaError,
    MAX_CODIGO_RETRIES,
    crear_mascota,
    listar_mascotas_por_usuario,
)
from app.services.usuario_service import UserError, update_fcm_token, update_ubicacion
from tests.conftest import _AlertRow


# ══════════════════════════════════════════════════════════════
# AuthService
# ══════════════════════════════════════════════════════════════


class TestAuthService:
    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.hash_password")
    @pytest.mark.asyncio
    async def test_register_success(self, mock_hash, mock_create_token, mock_db_session):
        """Register a new user — no existing user, returns token."""
        mock_hash.return_value = "hashed_123"
        mock_create_token.return_value = "jwt_token"
        # No existing user
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await register(
            db=mock_db_session,
            correo="new@test.com",
            contrasena="123456",
            nombre="New User",
        )

        mock_hash.assert_called_once_with("123456")
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        mock_create_token.assert_called_once()
        assert result["access_token"] == "jwt_token"
        assert result["token_type"] == "bearer"

    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.hash_password")
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_hash, mock_create_token, mock_db_session):
        """Register with an existing email raises AuthError(400)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = MagicMock()

        with pytest.raises(AuthError) as exc:
            await register(
                db=mock_db_session,
                correo="existing@test.com",
                contrasena="123456",
                nombre="User",
            )

        assert exc.value.status_code == 400
        assert "ya está registrado" in exc.value.detail
        mock_db_session.add.assert_not_called()

    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.verify_password")
    @pytest.mark.asyncio
    async def test_login_success(self, mock_verify, mock_create_token, mock_db_session):
        """Login with correct credentials returns a token."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.contrasena_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_verify.return_value = True
        mock_create_token.return_value = "jwt_token"

        result = await login(
            db=mock_db_session, correo="user@test.com", contrasena="correct_pass"
        )

        mock_verify.assert_called_once_with("correct_pass", "hashed_pass")
        mock_create_token.assert_called_once_with({"sub": "1"})
        assert result["access_token"] == "jwt_token"
        assert result["token_type"] == "bearer"

    @patch("app.services.auth_service.verify_password")
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, mock_verify, mock_db_session):
        """Login with wrong password raises AuthError(401)."""
        mock_user = MagicMock()
        mock_user.contrasena_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_verify.return_value = False

        with pytest.raises(AuthError) as exc:
            await login(
                db=mock_db_session, correo="user@test.com", contrasena="wrong_pass"
            )

        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, mock_db_session):
        """Login with non-existent email raises AuthError(401)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(AuthError) as exc:
            await login(
                db=mock_db_session, correo="noone@test.com", contrasena="123456"
            )

        assert exc.value.status_code == 401

    @patch("app.services.auth_service.create_access_token")
    @patch("app.services.auth_service.verify_password")
    @pytest.mark.asyncio
    async def test_login_autoridad_success(self, mock_verify, mock_create_token, mock_db_session):
        """Authority login with correct credentials returns a token with tipo=autoridad."""
        mock_autoridad = MagicMock()
        mock_autoridad.id = 1
        mock_autoridad.password_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_autoridad
        mock_verify.return_value = True
        mock_create_token.return_value = "jwt_autoridad"

        result = await login_autoridad(
            db=mock_db_session, email="policia@test.com", contrasena="correct_pass"
        )

        mock_verify.assert_called_once_with("correct_pass", "hashed_pass")
        mock_create_token.assert_called_once_with({"sub": "1", "tipo": "autoridad"})
        assert result["access_token"] == "jwt_autoridad"
        assert result["token_type"] == "bearer"

    @patch("app.services.auth_service.verify_password")
    @pytest.mark.asyncio
    async def test_login_autoridad_wrong_credentials(self, mock_verify, mock_db_session):
        """Authority login with wrong credentials raises AuthError(401)."""
        mock_autoridad = MagicMock()
        mock_autoridad.password_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_autoridad
        mock_verify.return_value = False

        with pytest.raises(AuthError) as exc:
            await login_autoridad(
                db=mock_db_session, email="policia@test.com", contrasena="wrong"
            )

        assert exc.value.status_code == 401


# ══════════════════════════════════════════════════════════════
# MascotaService
# ══════════════════════════════════════════════════════════════


class TestMascotaService:
    @pytest.mark.asyncio
    async def test_crear_mascota_nueva(self, mock_db_session):
        """Creating a mascota that doesn't exist yet succeeds."""
        datos = MascotaRequest(nombre="Fido", especie="perro", raza="Lab", color="Negro")
        # First execute returns None (no existing mascota)
        # Second execute (code uniqueness check) also returns None

        result = await crear_mascota(db=mock_db_session, usuario_id=1, datos=datos)

        assert result.nombre == "Fido"
        assert result.especie == "perro"
        assert result.raza == "Lab"
        assert result.color == "Negro"
        assert result.usuario_id == 1
        assert mock_db_session.add.called
        assert mock_db_session.flush.called
        # execute was called at least twice (existing check + code uniqueness)
        assert mock_db_session.execute.call_count >= 2

    @pytest.mark.asyncio
    async def test_crear_mascota_existente(self, mock_db_session):
        """Creating a mascota that already exists returns the existing one."""
        existing = MagicMock()
        existing.id = 10
        existing.nombre = "Fido"
        existing.especie = "perro"

        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing
        datos = MascotaRequest(nombre="Fido", especie="perro")

        result = await crear_mascota(db=mock_db_session, usuario_id=1, datos=datos)

        assert result.id == 10
        assert result.nombre == "Fido"
        assert mock_db_session.add.call_count == 0
        assert mock_db_session.flush.call_count == 0
        # Only the first execute (existing check) was called
        assert mock_db_session.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_listar_mascotas_por_usuario(self, mock_db_session):
        """Returns list of mascotas for a user."""
        mascota_1 = MagicMock()
        mascota_1.id = 1
        mascota_2 = MagicMock()
        mascota_2.id = 2

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
            mascota_1,
            mascota_2,
        ]

        result = await listar_mascotas_por_usuario(db=mock_db_session, usuario_id=1)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    @pytest.mark.asyncio
    async def test_listar_mascotas_por_usuario_empty(self, mock_db_session):
        """Returns empty list when user has no mascotas."""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

        result = await listar_mascotas_por_usuario(db=mock_db_session, usuario_id=1)

        assert result == []

    @pytest.mark.asyncio
    async def test_crear_mascota_max_retries_exhausted(self, mock_db_session):
        """Exhaust all retries for codigo_emergencia uniqueness → MascotaError."""
        datos = MascotaRequest(nombre="Unique", especie="perro")

        # First call (existing mascota check) returns None → passes through
        # Subsequent calls (codigo_emergencia check) return MagicMock → always "exists"
        mock_db_session.execute.return_value.scalar_one_or_none.side_effect = [
            None
        ] + [MagicMock()] * MAX_CODIGO_RETRIES

        with pytest.raises(MascotaError) as exc:
            await crear_mascota(db=mock_db_session, usuario_id=1, datos=datos)

        assert exc.value.status_code == 500
        assert "No se pudo generar" in exc.value.detail
        # One execute for the existing check + MAX_CODIGO_RETRIES attempts
        assert mock_db_session.execute.call_count == 1 + MAX_CODIGO_RETRIES


# ══════════════════════════════════════════════════════════════
# UsuarioService
# ══════════════════════════════════════════════════════════════


class TestUsuarioService:
    @pytest.mark.asyncio
    async def test_update_ubicacion_success(self, mock_db_session):
        """Update ubicacion for existing user."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.ubicacion = None
        mock_db_session.get.return_value = mock_user

        result = await update_ubicacion(
            db=mock_db_session, usuario_id=1, lat=-34.5, lon=-58.3
        )

        assert result.id == 1
        assert result.ubicacion is not None
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_ubicacion_user_not_found(self, mock_db_session):
        """Update ubicacion for non-existent user raises UserError(404)."""
        mock_db_session.get.return_value = None

        with pytest.raises(UserError) as exc:
            await update_ubicacion(
                db=mock_db_session, usuario_id=999, lat=0.0, lon=0.0
            )

        assert exc.value.status_code == 404
        mock_db_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_fcm_token_success(self, mock_db_session):
        """Update FCM token for existing user."""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.fcm_token = None
        mock_db_session.get.return_value = mock_user

        result = await update_fcm_token(
            db=mock_db_session, usuario_id=1, fcm_token="new_token"
        )

        assert result.fcm_token == "new_token"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_user)

    @pytest.mark.asyncio
    async def test_update_fcm_token_user_not_found(self, mock_db_session):
        """Update FCM token for non-existent user raises UserError(404)."""
        mock_db_session.get.return_value = None

        with pytest.raises(UserError) as exc:
            await update_fcm_token(
                db=mock_db_session, usuario_id=999, fcm_token="tok"
            )

        assert exc.value.status_code == 404
        mock_db_session.commit.assert_not_called()


# ══════════════════════════════════════════════════════════════
# AlertaService
# ══════════════════════════════════════════════════════════════


class TestAlertaService:
    @patch("app.services.alerta_service.crear_mascota")
    @patch("app.services.alerta_service.notificar_radio_inicial")
    @patch("app.services.alerta_service.expandir_radio")
    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_crear_alerta_success(
        self,
        mock_broadcast,
        mock_expandir,
        mock_notificar,
        mock_crear_mascota,
        mock_db_session,
    ):
        """Creating an alerta succeeds with mascota, Celery tasks, and broadcast."""
        mock_mascota = MagicMock()
        mock_mascota.id = 1
        mock_mascota.codigo_emergencia = "ABC123"
        mock_mascota.nombre = "Fido"
        mock_mascota.especie = "perro"
        mock_crear_mascota.return_value = mock_mascota

        # Mock Alerta constructor to return a controlled mock
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.radio_actual_km = 1
        mock_alerta.mascota_id = 1
        mock_alerta.descripcion = "Test desc"
        mock_alerta.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

        datos = AlertaRequest(
            mascota={"nombre": "Fido", "especie": "perro"},
            ubicacion={"lat": -34.5, "lon": -58.3},
            descripcion="Test desc",
        )

        with patch("app.services.alerta_service.Alerta", return_value=mock_alerta):
            result = await crear_alerta(db=mock_db_session, usuario_id=1, datos=datos)

        mock_crear_mascota.assert_called_once_with(
            db=mock_db_session, usuario_id=1, datos=datos.mascota
        )
        mock_db_session.add.assert_called_once_with(mock_alerta)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_alerta)

        mock_expandir.apply_async.assert_called_once()
        assert mock_expandir.apply_async.call_args[1]["args"] == [1]
        assert "countdown" in mock_expandir.apply_async.call_args[1]

        mock_notificar.apply_async.assert_called_once_with(
            args=[1], countdown=0
        )

        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][0]
        assert broadcast_data["type"] == "nueva_alerta"
        assert broadcast_data["alerta_id"] == 1
        assert broadcast_data["mascota_nombre"] == "Fido"

        assert result["alerta_id"] == 1
        assert result["estado"] == "ACTIVA_1KM"
        assert result["codigo_emergencia"] == "ABC123"

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_resolver_alerta_owner_success(
        self, mock_broadcast, mock_db_session
    ):
        """Owner can resolve their own alerta."""
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.radio_actual_km = 1
        mock_alerta.resuelta_en = None
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        result = await resolver_alerta(
            db=mock_db_session, alerta_id=1, usuario_id=1, es_autoridad=False
        )

        assert result["alerta_id"] == 1
        assert result["estado"] == "RESUELTA"
        assert "resuelta_en" in result
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_alerta)
        mock_broadcast.assert_called_once()
        assert mock_broadcast.call_args[0][0]["type"] == "alerta_resuelta"

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_resolver_alerta_authority_success(
        self, mock_broadcast, mock_db_session
    ):
        """Authority can resolve any alerta even if not the owner."""
        mock_alerta = MagicMock()
        mock_alerta.id = 2
        mock_alerta.usuario_id = 999  # Not the authority's ID
        mock_alerta.estado = "ACTIVA_5KM"
        mock_alerta.resuelta_en = None
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        result = await resolver_alerta(
            db=mock_db_session, alerta_id=2, usuario_id=1, es_autoridad=True
        )

        assert result["estado"] == "RESUELTA"
        assert result["alerta_id"] == 2
        mock_broadcast.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolver_alerta_not_found(self, mock_db_session):
        """Resolving a non-existent alerta raises AlertaError(404)."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(AlertaError) as exc:
            await resolver_alerta(
                db=mock_db_session, alerta_id=999, usuario_id=1, es_autoridad=False
            )

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_resolver_alerta_not_owner(self, mock_db_session):
        """Non-owner without authority raises AlertaError(403)."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 2  # Different user
        mock_alerta.estado = "ACTIVA_1KM"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        with pytest.raises(AlertaError) as exc:
            await resolver_alerta(
                db=mock_db_session, alerta_id=1, usuario_id=1, es_autoridad=False
            )

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_resolver_alerta_already_resolved(self, mock_db_session):
        """Resolving an already-resolved alerta raises AlertaError(400)."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "RESUELTA"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        with pytest.raises(AlertaError) as exc:
            await resolver_alerta(
                db=mock_db_session, alerta_id=1, usuario_id=1, es_autoridad=False
            )

        assert exc.value.status_code == 400

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_cancelar_alerta_success(self, mock_broadcast, mock_db_session):
        """Owner can cancel their own active alerta."""
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.resuelta_en = None
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        result = await cancelar_alerta(
            db=mock_db_session, alerta_id=1, usuario_id=1
        )

        assert result["alerta_id"] == 1
        assert result["estado"] == "CANCELADA"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_alerta)
        mock_broadcast.assert_called_once()
        assert mock_broadcast.call_args[0][0]["type"] == "alerta_cancelada"

    @pytest.mark.asyncio
    async def test_cancelar_alerta_not_owner(self, mock_db_session):
        """Non-owner cannot cancel an alerta — raises AlertaError(403)."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 2
        mock_alerta.estado = "ACTIVA_1KM"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        with pytest.raises(AlertaError) as exc:
            await cancelar_alerta(
                db=mock_db_session, alerta_id=1, usuario_id=1
            )

        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cancelar_alerta_already_resolved(self, mock_db_session):
        """Cancelling a resolved alerta raises AlertaError(400)."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "RESUELTA"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        with pytest.raises(AlertaError) as exc:
            await cancelar_alerta(
                db=mock_db_session, alerta_id=1, usuario_id=1
            )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_cancelar_alerta_already_cancelled(self, mock_db_session):
        """Cancelling a cancelled alerta raises AlertaError(400)."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "CANCELADA"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        with pytest.raises(AlertaError) as exc:
            await cancelar_alerta(
                db=mock_db_session, alerta_id=1, usuario_id=1
            )

        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_listar_alertas_activas_service(self, mock_db_session):
        """Returns list of active alertas."""
        row_1 = _AlertRow()
        row_1.id = 1
        row_1.mascota_id = 1
        row_1.estado = "ACTIVA_1KM"
        row_1.radio_actual_km = 1
        row_1.descripcion = "Desc 1"
        row_1.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        row_1.lat = -34.5
        row_1.lon = -58.3
        row_1.mascota_nombre = "Fido"
        row_1.mascota_especie = "perro"

        row_2 = _AlertRow()
        row_2.id = 2
        row_2.mascota_id = 2
        row_2.estado = "ACTIVA_5KM"
        row_2.radio_actual_km = 5
        row_2.descripcion = None
        row_2.created_at = datetime(2024, 6, 1, 13, 0, 0, tzinfo=timezone.utc)
        row_2.lat = 10.0
        row_2.lon = 20.0
        row_2.mascota_nombre = "Misi"
        row_2.mascota_especie = "gato"

        # The query returns Row objects with tuple-like access + named attrs
        mock_db_session.execute.return_value.all.return_value = [row_1, row_2]

        result = await listar_alertas_activas_service(db=mock_db_session)

        assert len(result) == 2
        assert result[0]["alerta_id"] == 1
        assert result[0]["estado"] == "ACTIVA_1KM"
        assert result[0]["mascota_nombre"] == "Fido"
        assert result[1]["alerta_id"] == 2
        assert result[1]["mascota_especie"] == "gato"

    @pytest.mark.asyncio
    async def test_listar_alertas_activas_service_empty(self, mock_db_session):
        """Returns empty list when no active alertas."""
        mock_db_session.execute.return_value.all.return_value = []

        result = await listar_alertas_activas_service(db=mock_db_session)

        assert result == []
