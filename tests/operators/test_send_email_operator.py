"""
Unit tests for MailtrapSendEmailOperator.

Run tests:
    pytest tests/operators/test_send_email_operator.py -v
"""

from unittest import mock

from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator


class TestMailtrapSendEmailOperator:
    """Test MailtrapSendEmailOperator functionality."""

    def test_operator_initialization(self):
        """Test operator initializes with correct parameters."""
        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test Subject",
            text="Test body",
            sender="sender@example.com",
            sender_name="Test Sender",
            category="test-category",
        )

        assert operator.to == "recipient@example.com"
        assert operator.subject == "Test Subject"
        assert operator.text == "Test body"
        assert operator.sender == "sender@example.com"
        assert operator.sender_name == "Test Sender"
        assert operator.category == "test-category"
        assert operator.mailtrap_conn_id == "mailtrap_default"

    def test_operator_custom_connection(self):
        """Test operator with custom connection ID."""
        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test",
            text="Body",
            mailtrap_conn_id="custom_mailtrap",
        )

        assert operator.mailtrap_conn_id == "custom_mailtrap"

    def test_template_fields(self):
        """Test that template_fields contains expected fields."""
        expected_fields = ("to", "subject", "text", "html", "sender", "sender_name", "category")

        assert MailtrapSendEmailOperator.template_fields == expected_fields

    @mock.patch("mailtrap_provider.operators.send_email.MailtrapHook")
    def test_execute_calls_hook(self, mock_hook_class):
        """Test that execute calls the hook's send_email method."""
        mock_hook = mock.MagicMock()
        mock_hook.send_email.return_value = {
            "success": True,
            "message_ids": ["msg-123"],
        }
        mock_hook_class.return_value = mock_hook

        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test Subject",
            text="Test body",
            sender="sender@example.com",
        )

        result = operator.execute(context={})

        mock_hook_class.assert_called_once_with(mailtrap_conn_id="mailtrap_default")
        mock_hook.send_email.assert_called_once_with(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            text="Test body",
            html=None,
            sender_name=None,
            category=None,
        )
        assert result["success"] is True
        assert result["message_ids"] == ["msg-123"]

    @mock.patch("mailtrap_provider.operators.send_email.MailtrapHook")
    def test_execute_with_html(self, mock_hook_class):
        """Test execute with HTML body."""
        mock_hook = mock.MagicMock()
        mock_hook.send_email.return_value = {"success": True, "message_ids": []}
        mock_hook_class.return_value = mock_hook

        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test Subject",
            html="<h1>Hello</h1>",
            sender="sender@example.com",
        )

        operator.execute(context={})

        mock_hook.send_email.assert_called_once_with(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            text=None,
            html="<h1>Hello</h1>",
            sender_name=None,
            category=None,
        )

    @mock.patch("mailtrap_provider.operators.send_email.MailtrapHook")
    def test_execute_with_multiple_recipients(self, mock_hook_class):
        """Test execute with multiple recipients."""
        mock_hook = mock.MagicMock()
        mock_hook.send_email.return_value = {"success": True, "message_ids": []}
        mock_hook_class.return_value = mock_hook

        recipients = ["user1@example.com", "user2@example.com"]
        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to=recipients,
            subject="Test Subject",
            text="Test body",
            sender="sender@example.com",
        )

        operator.execute(context={})

        mock_hook.send_email.assert_called_once()
        call_kwargs = mock_hook.send_email.call_args[1]
        assert call_kwargs["to"] == recipients

    @mock.patch("mailtrap_provider.operators.send_email.MailtrapHook")
    def test_execute_with_all_parameters(self, mock_hook_class):
        """Test execute with all parameters provided."""
        mock_hook = mock.MagicMock()
        mock_hook.send_email.return_value = {"success": True, "message_ids": ["msg-456"]}
        mock_hook_class.return_value = mock_hook

        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test Subject",
            text="Plain text",
            html="<p>HTML</p>",
            sender="sender@example.com",
            sender_name="Test Sender",
            category="test-category",
            mailtrap_conn_id="custom_conn",
        )

        result = operator.execute(context={})

        mock_hook_class.assert_called_once_with(mailtrap_conn_id="custom_conn")
        mock_hook.send_email.assert_called_once_with(
            sender="sender@example.com",
            to="recipient@example.com",
            subject="Test Subject",
            text="Plain text",
            html="<p>HTML</p>",
            sender_name="Test Sender",
            category="test-category",
        )
        assert result["message_ids"] == ["msg-456"]

    @mock.patch("mailtrap_provider.operators.send_email.MailtrapHook")
    def test_execute_returns_response(self, mock_hook_class):
        """Test that execute returns the hook response for XCom."""
        mock_hook = mock.MagicMock()
        expected_response = {
            "success": True,
            "message_ids": ["msg-abc", "msg-def"],
        }
        mock_hook.send_email.return_value = expected_response
        mock_hook_class.return_value = mock_hook

        operator = MailtrapSendEmailOperator(
            task_id="test_task",
            to="recipient@example.com",
            subject="Test",
            text="Body",
            sender="sender@example.com",
        )

        result = operator.execute(context={})

        assert result == expected_response

    def test_ui_color(self):
        """Test that operator has Mailtrap green color."""
        assert MailtrapSendEmailOperator.ui_color == "#22d172"
