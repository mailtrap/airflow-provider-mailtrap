"""Mailtrap Send Email Operator for Apache Airflow."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from airflow.models import BaseOperator

from mailtrap_provider.hooks.mailtrap import MailtrapHook

if TYPE_CHECKING:
    from airflow.utils.context import Context


class MailtrapSendEmailOperator(BaseOperator):
    """
    Send an email via Mailtrap.io transactional email service.

    This operator uses the Mailtrap API to send transactional emails.
    It supports plain text and HTML email bodies, single or multiple recipients.

    :param to: Recipient email address(es). Can be a single email string or list of emails.
    :param subject: Email subject line.
    :param text: Plain text email body. At least one of text or html must be provided.
    :param html: HTML email body. At least one of text or html must be provided.
    :param sender: Sender email address. Falls back to connection extra if not provided.
    :param sender_name: Optional display name for the sender.
    :param category: Optional category for Mailtrap analytics.
    :param mailtrap_conn_id: Connection ID for Mailtrap credentials.

    Example usage:

    .. code-block:: python

        from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator

        send_email = MailtrapSendEmailOperator(
            task_id="send_welcome_email",
            to="user@example.com",
            subject="Welcome!",
            html="<h1>Welcome to our service!</h1>",
            sender="noreply@yourdomain.com",
        )
    """

    template_fields: Sequence[str] = (
        "to",
        "subject",
        "text",
        "html",
        "sender",
        "sender_name",
        "category",
    )
    template_fields_renderers = {"html": "html", "text": "txt"}
    ui_color = "#22d172"  # Mailtrap green

    def __init__(
        self,
        *,
        to: str | list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
        sender: str | None = None,
        sender_name: str | None = None,
        category: str | None = None,
        mailtrap_conn_id: str = MailtrapHook.default_conn_name,
        **kwargs: Any,
    ) -> None:
        """Initialize the MailtrapSendEmailOperator."""
        super().__init__(**kwargs)
        self.to = to
        self.subject = subject
        self.text = text
        self.html = html
        self.sender = sender
        self.sender_name = sender_name
        self.category = category
        self.mailtrap_conn_id = mailtrap_conn_id

    def execute(self, context: Context) -> dict[str, Any]:
        """
        Execute the operator - send email via Mailtrap.

        :param context: Airflow task context.
        :return: Response from Mailtrap API containing message IDs.
        """
        hook = MailtrapHook(mailtrap_conn_id=self.mailtrap_conn_id)

        self.log.info(
            "Sending email via Mailtrap: subject='%s', to=%s",
            self.subject,
            self.to if isinstance(self.to, str) else ", ".join(self.to),
        )

        response = hook.send_email(
            sender=self.sender,
            to=self.to,
            subject=self.subject,
            text=self.text,
            html=self.html,
            sender_name=self.sender_name,
            category=self.category,
        )

        return response
