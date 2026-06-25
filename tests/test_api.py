"""Tests for API endpoints via TestClient — auth, users, mascotas, alertas, health."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from tests.conftest import _AlertRow


# ══════════════════════════════════════════════════════════════
# Auth endpoints
# ══════════════════════════════════════════════════════════════


class TestAuthAPI:
    AUTH_REGISTRO = "/auth/registro"
    AUTH_LOGIN = "/auth/login"
    AUTH_LOGIN_AUTORIDAD = "/auth/login-autoridad"

    def test_registro_success(self, test_client, mock_db_session):
        """POST /auth/registro — success creates user and returns token."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        response = test_client.post(
            self.AUTH_REGISTRO,
            json={
                "correo": "new@user.com",
                "contrasena": "123456",
                "nombre": "New User",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_registro_duplicate_email(self, test_client, mock_db_session):
        """POST /auth/registro — duplicate email returns 400."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = MagicMock()

        response = test_client.post(
            self.AUTH_REGISTRO,
            json={
                "correo": "existing@user.com",
                "contrasena": "123456",
                "nombre": "Existing",
            },
        )

        assert response.status_code == 400
        assert "ya está registrado" in response.json()["detail"]

    def test_registro_missing_fields(self, test_client):
        """POST /auth/registro — missing required fields returns 422."""
        response = test_client.post(self.AUTH_REGISTRO, json={})
        assert response.status_code == 422

        response = test_client.post(
            self.AUTH_REGISTRO, json={"correo": "test@test.com"}
        )
        assert response.status_code == 422

    def test_registro_invalid_email(self, test_client):
        """POST /auth/registro — invalid email format returns 422."""
        response = test_client.post(
            self.AUTH_REGISTRO,
            json={
                "correo": "notanemail",
                "contrasena": "123456",
                "nombre": "User",
            },
        )
        assert response.status_code == 422

    def test_registro_short_password(self, test_client):
        """POST /auth/registro — password < 6 chars returns 422."""
        response = test_client.post(
            self.AUTH_REGISTRO,
            json={
                "correo": "test@test.com",
                "contrasena": "12345",
                "nombre": "User",
            },
        )
        assert response.status_code == 422

    @patch("app.services.auth_service.verify_password")
    def test_login_success(self, mock_verify, test_client, mock_db_session):
        """POST /auth/login — valid credentials return token."""
        mock_verify.return_value = True
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.contrasena_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        response = test_client.post(
            self.AUTH_LOGIN,
            json={"correo": "user@test.com", "contrasena": "correct_pass"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch("app.services.auth_service.verify_password")
    def test_login_invalid_credentials(self, mock_verify, test_client, mock_db_session):
        """POST /auth/login — wrong password returns 401."""
        mock_verify.return_value = False
        mock_user = MagicMock()
        mock_user.contrasena_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        response = test_client.post(
            self.AUTH_LOGIN,
            json={"correo": "user@test.com", "contrasena": "wrong"},
        )

        assert response.status_code == 401

    def test_login_user_not_found(self, test_client, mock_db_session):
        """POST /auth/login — non-existent user returns 401."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        response = test_client.post(
            self.AUTH_LOGIN,
            json={"correo": "noone@test.com", "contrasena": "123456"},
        )

        assert response.status_code == 401

    def test_login_missing_fields(self, test_client):
        """POST /auth/login — missing fields returns 422."""
        response = test_client.post(self.AUTH_LOGIN, json={})
        assert response.status_code == 422

    @patch("app.services.auth_service.verify_password")
    def test_login_autoridad_success(self, mock_verify, test_client, mock_db_session):
        """POST /auth/login-autoridad — valid authority credentials return token."""
        mock_verify.return_value = True
        mock_autoridad = MagicMock()
        mock_autoridad.id = 1
        mock_autoridad.password_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_autoridad

        response = test_client.post(
            self.AUTH_LOGIN_AUTORIDAD,
            json={"correo": "policia@test.com", "contrasena": "correct_pass"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch("app.services.auth_service.verify_password")
    def test_login_autoridad_wrong_credentials(self, mock_verify, test_client, mock_db_session):
        """POST /auth/login-autoridad — wrong credentials return 401."""
        mock_verify.return_value = False
        mock_autoridad = MagicMock()
        mock_autoridad.password_hash = "hashed_pass"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_autoridad

        response = test_client.post(
            self.AUTH_LOGIN_AUTORIDAD,
            json={"correo": "policia@test.com", "contrasena": "wrong"},
        )

        assert response.status_code == 401


# ══════════════════════════════════════════════════════════════
# User endpoints
# ══════════════════════════════════════════════════════════════


class TestUserAPI:
    USUARIOS_YO = "/usuarios/yo"
    USUARIOS_UBICACION = "/usuarios/yo/ubicacion"
    USUARIOS_FCM = "/usuarios/yo/fcm-token"

    def test_obtener_perfil_success(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """GET /usuarios/yo — returns authenticated user's profile."""
        response = test_client.get(self.USUARIOS_YO, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["correo"] == "test@test.com"
        assert data["nombre"] == "Test User"
        assert data["id"] == 1

    def test_obtener_perfil_unauthorized(self, test_client):
        """GET /usuarios/yo — returns 403 without auth headers (HTTPBearer)."""
        response = test_client.get(self.USUARIOS_YO)
        assert response.status_code == 403

    def test_obtener_perfil_invalid_token(self, test_client):
        """GET /usuarios/yo — returns 401 with invalid token."""
        response = test_client.get(
            self.USUARIOS_YO, headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_actualizar_ubicacion_success(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /usuarios/yo/ubicacion — updates location successfully."""
        response = test_client.put(
            self.USUARIOS_UBICACION,
            headers=auth_headers,
            json={"lat": -34.5, "lon": -58.3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["correo"] == "test@test.com"

    def test_actualizar_ubicacion_unauthorized(self, test_client):
        """PUT /usuarios/yo/ubicacion — returns 403 without auth (HTTPBearer)."""
        response = test_client.put(
            self.USUARIOS_UBICACION, json={"lat": 0.0, "lon": 0.0}
        )
        assert response.status_code == 403

    def test_actualizar_ubicacion_invalid_lat(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /usuarios/yo/ubicacion — invalid lat returns 422."""
        response = test_client.put(
            self.USUARIOS_UBICACION,
            headers=auth_headers,
            json={"lat": 100.0, "lon": 0.0},
        )
        assert response.status_code == 422

    def test_actualizar_ubicacion_invalid_lon(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /usuarios/yo/ubicacion — invalid lon returns 422."""
        response = test_client.put(
            self.USUARIOS_UBICACION,
            headers=auth_headers,
            json={"lat": 0.0, "lon": -200.0},
        )
        assert response.status_code == 422

    def test_actualizar_fcm_token_success(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /usuarios/yo/fcm-token — updates FCM token successfully."""
        response = test_client.put(
            self.USUARIOS_FCM,
            headers=auth_headers,
            json={"fcm_token": "new_fcm_token_value"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

    def test_actualizar_fcm_token_unauthorized(self, test_client):
        """PUT /usuarios/yo/fcm-token — returns 403 without auth (HTTPBearer)."""
        response = test_client.put(
            self.USUARIOS_FCM, json={"fcm_token": "tok"}
        )
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════
# Mascota endpoints
# ══════════════════════════════════════════════════════════════


class TestMascotaAPI:
    MASCOTAS = "/mascotas"

    def test_listar_mascotas_success(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """GET /mascotas — returns user's mascotas list."""
        mascota_1 = MagicMock()
        mascota_1.id = 1
        mascota_1.nombre = "Fido"
        mascota_1.especie = "perro"
        mascota_1.raza = None
        mascota_1.color = None
        mascota_1.codigo_emergencia = "ABC123"
        mascota_1.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

        # The listar_mascotas_por_usuario uses scalars().all()
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = [
            mascota_1
        ]

        response = test_client.get(self.MASCOTAS, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["nombre"] == "Fido"
        assert data[0]["especie"] == "perro"

    def test_listar_mascotas_empty(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """GET /mascotas — returns empty list when user has no mascotas."""
        mock_db_session.execute.return_value.scalars.return_value.all.return_value = []

        response = test_client.get(self.MASCOTAS, headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_mascotas_unauthorized(self, test_client):
        """GET /mascotas — returns 403 without auth (HTTPBearer)."""
        response = test_client.get(self.MASCOTAS)
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════
# Alerta endpoints
# ══════════════════════════════════════════════════════════════


class TestAlertaAPI:
    ALERTAS = "/alertas"
    ALERTAS_ACTIVAS = "/alertas/activas"

    @patch("app.services.alerta_service.Alerta")
    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    @patch("app.services.alerta_service.notificar_radio_inicial")
    @patch("app.services.alerta_service.expandir_radio")
    @patch("app.services.alerta_service.crear_mascota")
    def test_crear_alerta_success(
        self,
        mock_cm,
        mock_exp,
        mock_notif,
        mock_broadcast,
        mock_alerta_class,
        test_client,
        mock_db_session,
        mock_current_user,
        auth_headers,
    ):
        """POST /alertas — creates alerta and returns 201."""
        mock_mascota = MagicMock()
        mock_mascota.id = 1
        mock_mascota.codigo_emergencia = "XYZ789"
        mock_mascota.nombre = "Fido"
        mock_mascota.especie = "perro"
        mock_cm.return_value = mock_mascota

        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.radio_actual_km = 1
        mock_alerta.mascota_id = 1
        mock_alerta.descripcion = "Se perdio en el parque"
        mock_alerta.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_alerta_class.return_value = mock_alerta

        response = test_client.post(
            self.ALERTAS,
            headers=auth_headers,
            json={
                "mascota": {"nombre": "Fido", "especie": "perro"},
                "ubicacion": {"lat": -34.5, "lon": -58.3},
                "descripcion": "Se perdio en el parque",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["alerta_id"] == 1
        assert data["estado"] == "ACTIVA_1KM"
        assert data["codigo_emergencia"] == "XYZ789"

    def test_crear_alerta_unauthorized(self, test_client):
        """POST /alertas — returns 403 without auth (HTTPBearer)."""
        response = test_client.post(
            self.ALERTAS,
            json={
                "mascota": {"nombre": "Fido", "especie": "perro"},
                "ubicacion": {"lat": 0.0, "lon": 0.0},
            },
        )
        assert response.status_code == 403

    def test_crear_alerta_invalid_data(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """POST /alertas — invalid data returns 422."""
        # Invalid: empty mascota name
        response = test_client.post(
            self.ALERTAS,
            headers=auth_headers,
            json={
                "mascota": {"nombre": "", "especie": "perro"},
                "ubicacion": {"lat": 0.0, "lon": 0.0},
            },
        )
        assert response.status_code == 422

    def test_listar_alertas_activas_success(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """GET /alertas/activas — returns list of active alertas."""
        row = _AlertRow()
        row.id = 1
        row.mascota_id = 1
        row.estado = "ACTIVA_1KM"
        row.radio_actual_km = 1
        row.descripcion = "Test"
        row.created_at = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        row.lat = -34.5
        row.lon = -58.3
        row.mascota_nombre = "Fido"
        row.mascota_especie = "perro"

        mock_db_session.execute.return_value.all.return_value = [row]

        response = test_client.get(self.ALERTAS_ACTIVAS, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["alerta_id"] == 1
        assert data[0]["mascota_nombre"] == "Fido"
        assert data[0]["lat"] == -34.5

    def test_listar_alertas_activas_empty(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """GET /alertas/activas — returns empty list."""
        mock_db_session.execute.return_value.all.return_value = []

        response = test_client.get(self.ALERTAS_ACTIVAS, headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_listar_alertas_activas_unauthorized(self, test_client):
        """GET /alertas/activas — returns 403 without auth (HTTPBearer)."""
        response = test_client.get(self.ALERTAS_ACTIVAS)
        assert response.status_code == 403

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    def test_resolver_alerta_owner_success(
        self, mock_broadcast, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/resolver — owner can resolve."""
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.usuario_id = 1  # same as the owner
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.resuelta_en = None
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/1/resolver", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["alerta_id"] == 1
        assert data["estado"] == "RESUELTA"

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    def test_resolver_alerta_authority_success(
        self, mock_broadcast, test_client, mock_db_session, mock_current_authority, auth_headers_authority
    ):
        """PUT /alertas/{id}/resolver — authority can resolve any alerta."""
        mock_alerta = MagicMock()
        mock_alerta.id = 2
        mock_alerta.usuario_id = 999  # NOT the authority's ID
        mock_alerta.estado = "ACTIVA_1KM"
        mock_alerta.resuelta_en = None
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/2/resolver", headers=auth_headers_authority
        )

        assert response.status_code == 200
        assert response.json()["estado"] == "RESUELTA"

    def test_resolver_alerta_not_owner(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/resolver — non-owner gets 403."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 2  # Different user
        mock_alerta.estado = "ACTIVA_1KM"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/1/resolver", headers=auth_headers
        )

        assert response.status_code == 403

    def test_resolver_alerta_not_found(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/resolver — non-existent alerta gets 404."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        response = test_client.put(
            "/alertas/999/resolver", headers=auth_headers
        )

        assert response.status_code == 404

    def test_resolver_alerta_unauthorized(self, test_client):
        """PUT /alertas/{id}/resolver — returns 403 without auth (HTTPBearer)."""
        response = test_client.put("/alertas/1/resolver")
        assert response.status_code == 403

    @patch("app.services.websocket_manager.manager.broadcast", new_callable=AsyncMock)
    def test_cancelar_alerta_owner_success(
        self, mock_broadcast, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/cancelar — owner can cancel."""
        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/1/cancelar", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["estado"] == "CANCELADA"

    def test_cancelar_alerta_not_owner(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/cancelar — non-owner gets 403."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 2
        mock_alerta.estado = "ACTIVA_1KM"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/1/cancelar", headers=auth_headers
        )

        assert response.status_code == 403

    def test_cancelar_alerta_not_found(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/cancelar — non-existent alerta gets 404."""
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        response = test_client.put(
            "/alertas/999/cancelar", headers=auth_headers
        )

        assert response.status_code == 404

    def test_cancelar_alerta_already_resolved(
        self, test_client, mock_db_session, mock_current_user, auth_headers
    ):
        """PUT /alertas/{id}/cancelar — already resolved alerta gets 400."""
        mock_alerta = MagicMock()
        mock_alerta.usuario_id = 1
        mock_alerta.estado = "RESUELTA"
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_alerta

        response = test_client.put(
            "/alertas/1/cancelar", headers=auth_headers
        )

        assert response.status_code == 400

    def test_cancelar_alerta_unauthorized(self, test_client):
        """PUT /alertas/{id}/cancelar — returns 403 without auth (HTTPBearer)."""
        response = test_client.put("/alertas/1/cancelar")
        assert response.status_code == 403


# ══════════════════════════════════════════════════════════════
# Health endpoint
# ══════════════════════════════════════════════════════════════


class TestHealth:
    def test_health(self, test_client):
        """GET /health — returns status ok."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ══════════════════════════════════════════════════════════════
# WebSocket endpoint
# ══════════════════════════════════════════════════════════════


class TestAlertasWebSocket:
    """Tests for WebSocket /ws/alertas endpoint.

    The endpoint validates a JWT token with tipo='autoridad' via query param.
    Invalid or missing tokens get close code 4001.
    """

    WEBSOCKET_URL = "/ws/alertas"

    def test_connect_with_authority_token(self, test_client):
        """Valid authority token should accept the connection."""
        token = create_access_token({"sub": "1", "tipo": "autoridad"})
        with test_client.websocket_connect(
            f"{self.WEBSOCKET_URL}?token={token}"
        ):
            # Connection was accepted — no exception raised
            pass

    def test_connect_invalid_token(self, test_client):
        """Garbage token should close with code 4001."""
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with test_client.websocket_connect(
                f"{self.WEBSOCKET_URL}?token=not_a_real_token"
            ):
                pass
        assert exc_info.value.code == 4001

    def test_connect_non_authority_token(self, test_client):
        """Regular user token (no tipo=autoridad) should close with code 4001."""
        token = create_access_token({"sub": "1"})  # regular user
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with test_client.websocket_connect(
                f"{self.WEBSOCKET_URL}?token={token}"
            ):
                pass
        assert exc_info.value.code == 4001
