"""
Unit tests for MailtrapHook.

Run tests:
    pytest tests/hooks/test_mailtrap_hook.py -v
"""

from unittest import mock

import pytest
from airflow.exceptions import AirflowException
from airflow.models import Connection

from mailtrap_provider.hooks.mailtrap import MailtrapHook


class TestMailtrapHook:
    """Test MailtrapHook functionality."""

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_get_token_success(self, mock_get_connection):
        """Test successful token retrieval from connection."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-api-token",
        )

        hook = MailtrapHook()
        token = hook._get_token()

        assert token == "test-api-token"

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_get_token_missing(self, mock_get_connection):
        """Test error when token is missing from connection."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password=None,
        )

        hook = MailtrapHook()

        with pytest.raises(AirflowException, match="No API token found"):
            hook._get_token()

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_get_extras(self, mock_get_connection):
        """Test retrieval of extras from connection."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
            extra='{"sender": "test@example.com", "sender_name": "Test Sender"}',
        )

        hook = MailtrapHook()
        extras = hook._get_extras()

        assert extras["sender"] == "test@example.com"
        assert extras["sender_name"] == "Test Sender"

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_get_conn_returns_client(self, mock_get_connection):
        """Test that get_conn returns a MailtrapClient."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-api-token",
        )

        hook = MailtrapHook()
        client = hook.get_conn()

        # Verify it's a MailtrapClient instance
        import mailtrap as mt

        assert isinstance(client, mt.MailtrapClient)

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_get_conn_caches_client(self, mock_get_connection):
        """Test that get_conn caches the client instance."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-api-token",
        )

        hook = MailtrapHook()
        client1 = hook.get_conn()
        client2 = hook.get_conn()

        assert client1 is client2

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_conn")
    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_send_email_success(self, mock_get_connection, mock_get_conn):
        """Test successful email sending."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
            extra='{"sender": "default@example.com"}',
        )

        mock_client = mock.MagicMock()
        mock_client.send.return_value = {
            "success": True,
            "message_ids": ["msg-123"],
        }
        mock_get_conn.return_value = mock_client

        hook = MailtrapHook()
        response = hook.send_email(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            text="Test body",
        )

        assert response["success"] is True
        assert response["message_ids"] == ["msg-123"]
        mock_client.send.assert_called_once()

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_conn")
    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_send_email_uses_connection_sender(self, mock_get_connection, mock_get_conn):
        """Test that sender falls back to connection extra."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
            extra='{"sender": "default@example.com", "sender_name": "Default Name"}',
        )

        mock_client = mock.MagicMock()
        mock_client.send.return_value = {"success": True, "message_ids": []}
        mock_get_conn.return_value = mock_client

        hook = MailtrapHook()
        hook.send_email(
            to="recipient@example.com",
            subject="Test",
            text="Body",
        )

        # Verify the Mail object was created with connection sender
        call_args = mock_client.send.call_args
        mail = call_args[0][0]  # First positional argument
        assert mail.sender.email == "default@example.com"
        assert mail.sender.name == "Default Name"

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_send_email_missing_sender(self, mock_get_connection):
        """Test error when sender is not provided anywhere."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
        )

        hook = MailtrapHook()

        with pytest.raises(AirflowException, match="sender is required"):
            hook.send_email(
                to="recipient@example.com",
                subject="Test",
                text="Body",
            )

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_send_email_missing_body(self, mock_get_connection):
        """Test error when neither text nor html body is provided."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
        )

        hook = MailtrapHook()

        with pytest.raises(AirflowException, match="Either text or html body must be provided"):
            hook.send_email(
                sender="sender@example.com",
                to="recipient@example.com",
                subject="Test",
            )

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_conn")
    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_send_email_multiple_recipients(self, mock_get_connection, mock_get_conn):
        """Test sending email to multiple recipients."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="test-token",
        )

        mock_client = mock.MagicMock()
        mock_client.send.return_value = {"success": True, "message_ids": []}
        mock_get_conn.return_value = mock_client

        hook = MailtrapHook()
        hook.send_email(
            sender="sender@example.com",
            to=["recipient1@example.com", "recipient2@example.com"],
            subject="Test",
            text="Body",
        )

        call_args = mock_client.send.call_args
        mail = call_args[0][0]
        assert len(mail.to) == 2
        assert mail.to[0].email == "recipient1@example.com"
        assert mail.to[1].email == "recipient2@example.com"

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_connection_success(self, mock_get_connection, requests_mock):
        """Test successful connection test."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="valid-token",
        )
        requests_mock.get("https://mailtrap.io/api/accounts", json=[{"id": 1, "name": "Test"}])

        hook = MailtrapHook()
        success, message = hook.test_connection()

        assert success is True
        assert message == "Connection successful"

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_connection_invalid_token(self, mock_get_connection, requests_mock):
        """Test connection test with invalid token."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password="invalid-token",
        )
        requests_mock.get("https://mailtrap.io/api/accounts", status_code=401)

        hook = MailtrapHook()
        success, message = hook.test_connection()

        assert success is False
        assert "Invalid API token" in message

    @mock.patch("mailtrap_provider.hooks.mailtrap.MailtrapHook.get_connection")
    def test_connection_missing_token(self, mock_get_connection):
        """Test connection test with missing token."""
        mock_get_connection.return_value = Connection(
            conn_id="mailtrap_default",
            conn_type="mailtrap",
            password=None,
        )

        hook = MailtrapHook()
        success, message = hook.test_connection()

        assert success is False
        assert "No API token" in message

    def test_get_ui_field_behaviour(self):
        """Test UI field configuration."""
        ui_behaviour = MailtrapHook.get_ui_field_behaviour()

        assert "hidden_fields" in ui_behaviour
        assert "password" not in ui_behaviour["hidden_fields"]
        assert "port" in ui_behaviour["hidden_fields"]
        assert ui_behaviour["relabeling"]["password"] == "API Token"
