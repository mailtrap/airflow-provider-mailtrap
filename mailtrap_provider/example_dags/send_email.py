"""
Example DAG demonstrating how to send emails via Mailtrap.

Before running this DAG:
1. Create a Mailtrap connection in Airflow UI (Admin → Connections):
   - Connection Id: mailtrap_default
   - Connection Type: mailtrap
   - Password: Your Mailtrap API token
   - Extra (optional): {"sender": "noreply@yourdomain.com", "sender_name": "Your App"}

2. Set the Airflow Variable 'test_email_recipient' with your test email address:
   - Admin → Variables → Add
   - Key: test_email_recipient
   - Value: your-email@example.com
"""

from airflow.decorators import dag
from airflow.models import Variable
from pendulum import datetime

from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator


@dag(
    dag_id="mailtrap_send_email_example",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    default_args={"retries": 1},
    tags=["example", "mailtrap", "email"],
    doc_md=__doc__,
)
def mailtrap_send_email_example():
    """
    Example DAG for sending emails via Mailtrap.

    Demonstrates basic email sending with the MailtrapSendEmailOperator.
    """
    # Get recipient from Airflow Variable (set this in UI before running)
    recipient = Variable.get("test_email_recipient", default_var="recipient@example.com")

    # Example 1: Send a simple plain text email
    send_plain_text_email = MailtrapSendEmailOperator(
        task_id="send_plain_text_email",
        to=recipient,
        subject="Hello from Airflow!",
        text="This is a test email sent from Apache Airflow via Mailtrap.",
        sender="noreply@yourdomain.com",  # Or configure in connection extras
        sender_name="Airflow Notifications",
    )

    # Example 2: Send an HTML email
    send_html_email = MailtrapSendEmailOperator(
        task_id="send_html_email",
        to=recipient,
        subject="Welcome to Our Service",
        html="""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h1 style="color: #22d172;">Welcome!</h1>
                <p>This is a <strong>HTML email</strong> sent from Apache Airflow via Mailtrap.</p>
                <p>You can use this operator to send:</p>
                <ul>
                    <li>Notifications</li>
                    <li>Reports</li>
                    <li>Alerts</li>
                </ul>
            </body>
        </html>
        """,
        sender="noreply@yourdomain.com",
        sender_name="Airflow Notifications",
        category="welcome",  # For Mailtrap analytics
    )

    # Example 3: Send to multiple recipients
    send_to_multiple = MailtrapSendEmailOperator(
        task_id="send_to_multiple_recipients",
        to=[recipient],  # Add more emails to this list
        subject="Team Update from Airflow",
        text="This email was sent to multiple recipients.",
        sender="noreply@yourdomain.com",
    )

    # Run examples in sequence
    send_plain_text_email >> send_html_email >> send_to_multiple


mailtrap_send_email_example()
