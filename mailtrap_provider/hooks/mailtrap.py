"""Mailtrap Hook for Apache Airflow."""

from __future__ import annotations

import json
from typing import Any

import mailtrap as mt
import requests
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook


class MailtrapHook(BaseHook):
    """
    Hook for interacting with the Mailtrap.io email service.

    Uses the Mailtrap Python SDK to send transactional emails.

    :param mailtrap_conn_id: Connection ID for Mailtrap credentials.
        The connection should have the API token stored in the password field.
        Optional defaults (sender, sender_name) can be stored in the extra field as JSON.
    """

    conn_name_attr = "mailtrap_conn_id"
    default_conn_name = "mailtrap_default"
    conn_type = "mailtrap"
    hook_name = "Mailtrap"

    @staticmethod
    def get_ui_field_behaviour() -> dict[str, Any]:
        """Return custom field behavior for the connection form."""
        return {
            "hidden_fields": ["port", "login", "schema", "host"],
            "relabeling": {
                "password": "API Token",
            },
            "placeholders": {
                "password": "Your Mailtrap API token",
                "extra": json.dumps(
                    {
                        "sender": "noreply@yourdomain.com",
                        "sender_name": "Your App",
                    },
                    indent=4,
                ),
            },
        }

    def __init__(self, mailtrap_conn_id: str = default_conn_name) -> None:
        """
        Initialize the MailtrapHook.

        :param mailtrap_conn_id: Connection ID for Mailtrap credentials.
        """
        super().__init__()
        self.mailtrap_conn_id = mailtrap_conn_id
        self._client: mt.MailtrapClient | None = None

    def _get_token(self) -> str:
        """Get the API token from the connection."""
        conn = self.get_connection(self.mailtrap_conn_id)
        if not conn.password:
            raise AirflowException(
                f"No API token found in connection '{self.mailtrap_conn_id}'. "
                "Please set the API token in the password field."
            )
        return conn.password

    def _get_extras(self) -> dict[str, Any]:
        """Get extra configuration from the connection."""
        conn = self.get_connection(self.mailtrap_conn_id)
        return conn.extra_dejson or {}

    def get_conn(self) -> mt.MailtrapClient:
        """
        Return the Mailtrap client.

        Returns the raw MailtrapClient for advanced use cases.

        :return: MailtrapClient instance
        """
        if self._client is None:
            token = self._get_token()
            self._client = mt.MailtrapClient(token=token)
        return self._client

    def send_email(
        self,
        *,
        sender: str | None = None,
        to: str | list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
        sender_name: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email via Mailtrap.

        :param sender: Sender email address. Falls back to connection extra if not provided.
        :param to: Recipient email address(es). Can be a single email or list of emails.
        :param subject: Email subject line.
        :param text: Plain text email body.
        :param html: HTML email body.
        :param sender_name: Optional display name for the sender.
        :param category: Optional category for Mailtrap analytics.
        :return: Response from Mailtrap API containing message IDs.
        :raises AirflowException: If sender is not provided and not in connection extras,
            or if neither text nor html body is provided.
        """
        extras = self._get_extras()

        # Resolve sender - parameter takes precedence over connection extra
        resolved_sender = sender or extras.get("sender")
        if not resolved_sender:
            raise AirflowException(
                "sender is required - provide as parameter or in connection extras"
            )

        # Resolve sender_name - parameter takes precedence over connection extra
        resolved_sender_name = sender_name or extras.get("sender_name")

        # Validate body
        if not text and not html:
            raise AirflowException("Either text or html body must be provided")

        # Build recipient list
        if isinstance(to, str):
            recipients = [mt.Address(email=to)]
        else:
            recipients = [mt.Address(email=email) for email in to]

        # Build mail object
        mail = mt.Mail(
            sender=mt.Address(email=resolved_sender, name=resolved_sender_name),
            to=recipients,
            subject=subject,
            text=text or "",
            html=html or "",
            category=category or "",
        )

        # Send email
        client = self.get_conn()
        self.log.info(
            "Sending email via Mailtrap: subject='%s', to=%s",
            subject,
            to if isinstance(to, str) else ", ".join(to),
        )

        response = client.send(mail)

        self.log.info("Email sent successfully. Message IDs: %s", response.get("message_ids", []))
        return response

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the Mailtrap connection by validating the API token.

        Uses the Mailtrap accounts endpoint to verify the token is valid.

        :return: Tuple of (success, message)
        """
        try:
            token = self._get_token()
            response = requests.get(
                "https://mailtrap.io/api/accounts",
                headers={"Api-Token": token},
                timeout=10,
            )
            if response.status_code == 200:
                return True, "Connection successful"
            if response.status_code == 401:
                return False, "Authentication failed: Invalid API token"
            return False, f"Connection failed with status code: {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "Connection timed out"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {e}"
        except AirflowException as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"
