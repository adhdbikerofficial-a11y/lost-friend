"""Tests for all Pydantic V2 schemas — validation, coercion, edge cases."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.alerta import (
    AlertaActivaResponse,
    AlertaRequest,
    AlertaResponse,
    ResolveAlertResponse,
    UbicacionSchema,
)
from app.schemas.auth import LoginRequest, RegistroRequest, TokenResponse
from app.schemas.mascota import MascotaRequest, MascotaResponse
from app.schemas.usuario import FCMTokenUpdate, UbicacionUpdate, UsuarioResponse


# ──────────────────────────────────────────────
# Auth schemas
# ──────────────────────────────────────────────


class TestRegistroRequest:
    def test_valid_lowercases_email(self):
        data = RegistroRequest(
            correo="Test@Example.COM", contrasena="123456", nombre="User"
        )
        assert data.correo == "test@example.com"

    def test_invalid_email_with_leading_spaces(self):
        """Leading/trailing spaces fail validation (regex check before strip)."""
        with pytest.raises(ValidationError):
            RegistroRequest(
                correo="  user@example.com  ", contrasena="123456", nombre="User"
            )

    def test_invalid_email_no_at(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="invalid", contrasena="123456", nombre="User")

    def test_invalid_email_no_domain(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="user@", contrasena="123456", nombre="User")

    def test_invalid_email_with_spaces(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="user @example.com", contrasena="123456", nombre="User")

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="test@test.com", contrasena="12345", nombre="User")

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="test@test.com", contrasena="123456", nombre="  ")

    def test_empty_name_empty_string(self):
        with pytest.raises(ValidationError):
            RegistroRequest(correo="test@test.com", contrasena="123456", nombre="")

    def test_optional_telefono_none(self):
        data = RegistroRequest(
            correo="test@test.com", contrasena="123456", nombre="User"
        )
        assert data.telefono is None

    def test_optional_telefono_provided(self):
        data = RegistroRequest(
            correo="test@test.com",
            contrasena="123456",
            nombre="User",
            telefono="+5491112345678",
        )
        assert data.telefono == "+5491112345678"


class TestLoginRequest:
    def test_basic_construction(self):
        data = LoginRequest(correo="test@test.com", contrasena="secret")
        assert data.correo == "test@test.com"
        assert data.contrasena == "secret"


class TestTokenResponse:
    def test_basic_construction(self):
        data = TokenResponse(access_token="abc.def.ghi")
        assert data.access_token == "abc.def.ghi"
        assert data.token_type == "bearer"

    def test_custom_token_type(self):
        data = TokenResponse(access_token="xyz", token_type="custom")
        assert data.token_type == "custom"


# ──────────────────────────────────────────────
# Usuario schemas
# ──────────────────────────────────────────────


class TestUsuarioResponse:
    def test_from_attributes(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.id = 1
        mock.correo = "test@test.com"
        mock.nombre = "Test"
        mock.telefono = None
        mock.fcm_token = None
        mock.created_at = ts
        mock.updated_at = ts

        result = UsuarioResponse.model_validate(mock)
        assert result.id == 1
        assert result.correo == "test@test.com"
        assert result.nombre == "Test"
        assert result.telefono is None
        assert result.fcm_token is None
        assert result.created_at == ts
        assert result.updated_at == ts

    def test_from_attributes_with_values(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.id = 2
        mock.correo = "user@domain.com"
        mock.nombre = "Alice"
        mock.telefono = "555-0100"
        mock.fcm_token = "fcm_token_abc"
        mock.created_at = ts
        mock.updated_at = ts

        result = UsuarioResponse.model_validate(mock)
        assert result.telefono == "555-0100"
        assert result.fcm_token == "fcm_token_abc"

    def test_construct_directly(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = UsuarioResponse(
            id=1,
            correo="a@b.com",
            nombre="N",
            telefono=None,
            fcm_token="tok",
            created_at=ts,
            updated_at=ts,
        )
        assert result.id == 1
        assert result.correo == "a@b.com"


class TestUbicacionUpdate:
    def test_valid(self):
        data = UbicacionUpdate(lat=-34.5, lon=-58.3)
        assert data.lat == -34.5
        assert data.lon == -58.3

    def test_valid_boundaries(self):
        data = UbicacionUpdate(lat=90.0, lon=180.0)
        assert data.lat == 90.0
        assert data.lon == 180.0

        data = UbicacionUpdate(lat=-90.0, lon=-180.0)
        assert data.lat == -90.0
        assert data.lon == -180.0

    def test_lat_out_of_range_positive(self):
        with pytest.raises(ValidationError):
            UbicacionUpdate(lat=90.1, lon=0.0)

    def test_lat_out_of_range_negative(self):
        with pytest.raises(ValidationError):
            UbicacionUpdate(lat=-90.1, lon=0.0)

    def test_lon_out_of_range_positive(self):
        with pytest.raises(ValidationError):
            UbicacionUpdate(lat=0.0, lon=180.1)

    def test_lon_out_of_range_negative(self):
        with pytest.raises(ValidationError):
            UbicacionUpdate(lat=0.0, lon=-180.1)

    def test_zero_zero(self):
        data = UbicacionUpdate(lat=0.0, lon=0.0)
        assert data.lat == 0.0
        assert data.lon == 0.0


class TestFCMTokenUpdate:
    def test_basic_construction(self):
        data = FCMTokenUpdate(fcm_token="some_token_value")
        assert data.fcm_token == "some_token_value"

    def test_empty_string(self):
        data = FCMTokenUpdate(fcm_token="")
        assert data.fcm_token == ""


# ──────────────────────────────────────────────
# Mascota schemas
# ──────────────────────────────────────────────


class TestMascotaRequest:
    def test_valid_species_perro(self):
        data = MascotaRequest(nombre="Fido", especie="perro")
        assert data.especie == "perro"

    def test_valid_species_gato(self):
        data = MascotaRequest(nombre="Misi", especie="GATO")
        assert data.especie == "gato"

    def test_valid_species_conejo(self):
        data = MascotaRequest(nombre="Bunny", especie="Conejo")
        assert data.especie == "conejo"

    def test_valid_species_ave(self):
        data = MascotaRequest(nombre="Piolin", especie="AVE")
        assert data.especie == "ave"

    def test_valid_species_otro(self):
        data = MascotaRequest(nombre="Rocky", especie="Otro")
        assert data.especie == "otro"

    def test_invalid_species(self):
        with pytest.raises(ValidationError):
            MascotaRequest(nombre="X", especie="tigre")

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            MascotaRequest(nombre="  ", especie="perro")

    def test_empty_name_empty_string(self):
        with pytest.raises(ValidationError):
            MascotaRequest(nombre="", especie="perro")

    def test_especie_lowercased(self):
        data = MascotaRequest(nombre="Fido", especie="PERRO")
        assert data.especie == "perro"

        data = MascotaRequest(nombre="Fido", especie="GATO")
        assert data.especie == "gato"

    def test_optional_fields_none(self):
        data = MascotaRequest(nombre="Fido", especie="perro")
        assert data.raza is None
        assert data.color is None

    def test_optional_fields_provided(self):
        data = MascotaRequest(nombre="Fido", especie="perro", raza="Labrador", color="Negro")
        assert data.raza == "Labrador"
        assert data.color == "Negro"


class TestMascotaResponse:
    def test_from_attributes(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.id = 1
        mock.nombre = "Fido"
        mock.especie = "perro"
        mock.raza = None
        mock.color = None
        mock.codigo_emergencia = "ABC123"
        mock.created_at = ts

        result = MascotaResponse.model_validate(mock)
        assert result.id == 1
        assert result.nombre == "Fido"
        assert result.especie == "perro"
        assert result.raza is None
        assert result.color is None
        assert result.codigo_emergencia == "ABC123"
        assert result.created_at == ts

    def test_from_attributes_with_values(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.id = 2
        mock.nombre = "Misi"
        mock.especie = "gato"
        mock.raza = "Siames"
        mock.color = "Cafe"
        mock.codigo_emergencia = "DEF456"
        mock.created_at = ts

        result = MascotaResponse.model_validate(mock)
        assert result.raza == "Siames"
        assert result.color == "Cafe"

    def test_construct_directly(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = MascotaResponse(
            id=1,
            nombre="Fido",
            especie="perro",
            codigo_emergencia="ABC123",
            created_at=ts,
        )
        assert result.nombre == "Fido"


# ──────────────────────────────────────────────
# Alerta schemas
# ──────────────────────────────────────────────


class TestUbicacionSchema:
    def test_valid(self):
        data = UbicacionSchema(lat=-34.5, lon=-58.3)
        assert data.lat == -34.5
        assert data.lon == -58.3

    def test_valid_boundaries(self):
        data = UbicacionSchema(lat=90.0, lon=180.0)
        assert data.lat == 90.0

        data = UbicacionSchema(lat=-90.0, lon=-180.0)
        assert data.lat == -90.0

    def test_lat_out_of_range(self):
        with pytest.raises(ValidationError):
            UbicacionSchema(lat=100.0, lon=0.0)

    def test_lat_below_range(self):
        with pytest.raises(ValidationError):
            UbicacionSchema(lat=-100.0, lon=0.0)

    def test_lon_out_of_range(self):
        with pytest.raises(ValidationError):
            UbicacionSchema(lat=0.0, lon=200.0)

    def test_lon_below_range(self):
        with pytest.raises(ValidationError):
            UbicacionSchema(lat=0.0, lon=-200.0)


class TestAlertaRequest:
    def test_valid_with_descripcion(self):
        data = AlertaRequest(
            mascota={"nombre": "Fido", "especie": "perro"},
            ubicacion={"lat": -34.5, "lon": -58.3},
            descripcion="Se perdio cerca del parque",
        )
        assert data.mascota.nombre == "Fido"
        assert data.mascota.especie == "perro"
        assert data.ubicacion.lat == -34.5
        assert data.ubicacion.lon == -58.3
        assert data.descripcion == "Se perdio cerca del parque"

    def test_valid_without_descripcion(self):
        data = AlertaRequest(
            mascota={"nombre": "Misi", "especie": "gato"},
            ubicacion={"lat": 10.0, "lon": 20.0},
        )
        assert data.descripcion is None

    def test_invalid_mascota_empty_name(self):
        with pytest.raises(ValidationError):
            AlertaRequest(
                mascota={"nombre": "", "especie": "perro"},
                ubicacion={"lat": 0.0, "lon": 0.0},
            )

    def test_invalid_mascota_bad_species(self):
        with pytest.raises(ValidationError):
            AlertaRequest(
                mascota={"nombre": "X", "especie": "leon"},
                ubicacion={"lat": 0.0, "lon": 0.0},
            )

    def test_invalid_ubicacion_bad_lat(self):
        with pytest.raises(ValidationError):
            AlertaRequest(
                mascota={"nombre": "Fido", "especie": "perro"},
                ubicacion={"lat": 100.0, "lon": 0.0},
            )


class TestAlertaResponse:
    def test_from_attributes(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.alerta_id = 1
        mock.estado = "ACTIVA_1KM"
        mock.radio_actual_km = 1
        mock.mascota_id = 1
        mock.codigo_emergencia = "ABC123"
        mock.created_at = ts

        result = AlertaResponse.model_validate(mock)
        assert result.alerta_id == 1
        assert result.estado == "ACTIVA_1KM"
        assert result.radio_actual_km == 1
        assert result.mascota_id == 1
        assert result.codigo_emergencia == "ABC123"
        assert result.created_at == ts

    def test_construct_directly(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = AlertaResponse(
            alerta_id=1,
            estado="ACTIVA_5KM",
            radio_actual_km=5,
            mascota_id=2,
            codigo_emergencia="XYZ789",
            created_at=ts,
        )
        assert result.alerta_id == 1
        assert result.radio_actual_km == 5
        assert result.estado == "ACTIVA_5KM"


class TestAlertaActivaResponse:
    def test_from_attributes(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.alerta_id = 10
        mock.mascota_id = 3
        mock.estado = "ACTIVA_1KM"
        mock.radio_actual_km = 1
        mock.lat = -34.5
        mock.lon = -58.3
        mock.descripcion = "Cerca del rio"
        mock.created_at = ts
        mock.mascota_nombre = "Fido"
        mock.mascota_especie = "perro"

        result = AlertaActivaResponse.model_validate(mock)
        assert result.alerta_id == 10
        assert result.lat == -34.5
        assert result.lon == -58.3
        assert result.descripcion == "Cerca del rio"
        assert result.mascota_nombre == "Fido"
        assert result.mascota_especie == "perro"

    def test_from_attributes_descripcion_none(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock = MagicMock()
        mock.alerta_id = 11
        mock.mascota_id = 4
        mock.estado = "ACTIVA_5KM"
        mock.radio_actual_km = 5
        mock.lat = 10.0
        mock.lon = 20.0
        mock.descripcion = None
        mock.created_at = ts
        mock.mascota_nombre = "Misi"
        mock.mascota_especie = "gato"

        result = AlertaActivaResponse.model_validate(mock)
        assert result.descripcion is None

    def test_construct_directly(self):
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = AlertaActivaResponse(
            alerta_id=1,
            mascota_id=1,
            estado="ACTIVA_1KM",
            radio_actual_km=1,
            lat=-34.5,
            lon=-58.3,
            created_at=ts,
            mascota_nombre="Fido",
            mascota_especie="perro",
        )
        assert result.alerta_id == 1


class TestResolveAlertResponse:
    def test_basic_construction(self):
        data = ResolveAlertResponse(
            alerta_id=1, estado="RESUELTA", resuelta_en="2024-06-01T12:00:00+00:00"
        )
        assert data.alerta_id == 1
        assert data.estado == "RESUELTA"
        assert data.resuelta_en == "2024-06-01T12:00:00+00:00"
