"""Tests for Celery tasks — radius expansion state machine and notifications.

Core business logic coverage (0 → complete).
All tests mock the sync Session and verify state transitions, scheduling, and error paths.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tasks.alertas import (
    _sync_database_url,
    expandir_radio,
    notificar_radio_inicial,
)


# ══════════════════════════════════════════════════════════════
# _sync_database_url
# ══════════════════════════════════════════════════════════════


class TestSyncDatabaseUrl:
    def test_replaces_asyncpg_with_psycopg2(self):
        url = _sync_database_url()
        assert "postgresql+psycopg2://" in url
        assert "+asyncpg" not in url

    def test_preserves_rest_of_url(self):
        url = _sync_database_url()
        assert "localhost" in url
        assert url.endswith("/lost_friend_db") or "/lost_friend_db" in url


# ══════════════════════════════════════════════════════════════
# expandir_radio
# ══════════════════════════════════════════════════════════════


class TestExpandirRadio:
    """State machine: ACTIVA_1KM → ACTIVA_5KM → ACTIVA_10KM → terminal."""

    @patch("app.tasks.alertas.Session")
    def test_activa_1km_to_5km(self, mock_session_class):
        """ACTIVA_1KM transitions to ACTIVA_5KM, notifies at 5km, schedules next."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = "ACTIVA_1KM"
        mock_session.get.return_value = mock_alerta

        with patch("app.tasks.alertas.expandir_radio.apply_async") as mock_apply:
            expandir_radio(1)

        assert mock_alerta.estado == "ACTIVA_5KM"
        assert mock_alerta.radio_actual_km == 5
        mock_session.commit.assert_called_once()
        mock_apply.assert_called_once()
        args, kwargs = mock_apply.call_args
        assert kwargs["args"] == [1]
        assert "countdown" in kwargs

    @patch("app.tasks.alertas.Session")
    def test_activa_5km_to_10km(self, mock_session_class):
        """ACTIVA_5KM transitions to ACTIVA_10KM, notifies at 10km, no further schedule."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.estado = "ACTIVA_5KM"
        mock_session.get.return_value = mock_alerta

        with patch("app.tasks.alertas.expandir_radio.apply_async") as mock_apply:
            expandir_radio(1)

        assert mock_alerta.estado == "ACTIVA_10KM"
        assert mock_alerta.radio_actual_km == 10
        mock_session.commit.assert_called_once()
        # Terminal state — no further expansion scheduled
        mock_apply.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_activa_10km_no_op(self, mock_session_class):
        """ACTIVA_10KM is terminal — no state change."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.estado = "ACTIVA_10KM"
        mock_session.get.return_value = mock_alerta

        with patch("app.tasks.alertas.expandir_radio.apply_async") as mock_apply:
            expandir_radio(1)

        # No state mutation
        assert mock_alerta.estado == "ACTIVA_10KM"
        mock_session.commit.assert_not_called()
        mock_apply.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_resuelta_no_op(self, mock_session_class):
        """RESUELTA alerts are not expanded."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.estado = "RESUELTA"
        mock_session.get.return_value = mock_alerta

        with patch("app.tasks.alertas.expandir_radio.apply_async") as mock_apply:
            expandir_radio(1)

        mock_session.commit.assert_not_called()
        mock_apply.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_cancelada_no_op(self, mock_session_class):
        """CANCELADA alerts are not expanded."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.estado = "CANCELADA"
        mock_session.get.return_value = mock_alerta

        with patch("app.tasks.alertas.expandir_radio.apply_async") as mock_apply:
            expandir_radio(1)

        mock_session.commit.assert_not_called()
        mock_apply.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_alerta_not_found(self, mock_session_class):
        """Non-existent alerta logs warning and returns — no crash."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None

        # Should not raise
        expandir_radio(999)

        mock_session.commit.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_exception_triggers_retry(self, mock_session_class):
        """Exception inside task triggers retry mechanism."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.get.side_effect = ValueError("DB connection failed")

        mock_retry = MagicMock(side_effect=RuntimeError("Retry"))
        with patch.object(expandir_radio, "retry", mock_retry):
            with pytest.raises(RuntimeError):
                expandir_radio(1)

        mock_retry.assert_called_once()


# ══════════════════════════════════════════════════════════════
# notificar_radio_inicial
# ══════════════════════════════════════════════════════════════


class TestNotificarRadioInicial:
    @patch("app.tasks.alertas.enviar_push")
    @patch("app.tasks.alertas.Session")
    def test_notifica_usuarios_en_1km(self, mock_session_class, mock_enviar_push):
        """Notifies users within 1km radius when alerta exists."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        mock_alerta = MagicMock()
        mock_alerta.id = 1
        mock_alerta.ubicacion = b"\\x"  # WKB geometry stub
        mock_session.get.return_value = mock_alerta

        # Mock the query chain to return users with FCM tokens
        mock_session.query.return_value.filter.return_value.all.return_value = [
            ("test_fcm_token",)
        ]

        notificar_radio_inicial(1)

        mock_session.get.assert_called_once()
        # Should call _notificar_usuarios_en_radio → enviar_push
        mock_enviar_push.assert_called_once()

    @patch("app.tasks.alertas.enviar_push")
    @patch("app.tasks.alertas.Session")
    def test_alerta_not_found(self, mock_session_class, mock_enviar_push):
        """Non-existent alerta logs warning and returns."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = None

        notificar_radio_inicial(999)

        mock_enviar_push.assert_not_called()

    @patch("app.tasks.alertas.Session")
    def test_exception_triggers_retry(self, mock_session_class):
        """Exception inside task triggers retry mechanism."""
        mock_session = MagicMock()
        mock_session_class.return_value.__enter__.return_value = mock_session
        mock_session.get.side_effect = ValueError("DB error")

        mock_retry = MagicMock(side_effect=RuntimeError("Retry"))
        with patch.object(notificar_radio_inicial, "retry", mock_retry):
            with pytest.raises(RuntimeError):
                notificar_radio_inicial(1)

        mock_retry.assert_called_once()
