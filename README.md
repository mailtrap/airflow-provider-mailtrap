# Mailtrap Airflow Provider

[![PyPI version](https://badge.fury.io/py/airflow-provider-mailtrap.svg)](https://badge.fury.io/py/airflow-provider-mailtrap)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

An Apache Airflow provider for [Mailtrap.io](https://mailtrap.io) - send transactional emails from your Airflow DAGs.

## Installation

```bash
pip install airflow-provider-mailtrap
```

## Requirements

- Python >= 3.9
- Apache Airflow >= 2.4
- Mailtrap API token ([get one here](https://mailtrap.io/api-tokens))

## Setup

### 1. Create a Mailtrap Connection

In the Airflow UI, go to **Admin → Connections → Add**:

| Field                | Value                                                             |
| -------------------- | ----------------------------------------------------------------- |
| **Connection Id**    | `mailtrap_default`                                                |
| **Connection Type**  | `mailtrap`                                                        |
| **Password**         | Your Mailtrap API token                                           |
| **Extra** (optional) | `{"sender": "noreply@yourdomain.com", "sender_name": "Your App"}` |

### 2. Use the Operator in Your DAG

```python
from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator

send_email = MailtrapSendEmailOperator(
    task_id="send_welcome_email",
    to="user@example.com",
    subject="Welcome!",
    html="<h1>Welcome to our service!</h1>",
    sender="noreply@yourdomain.com",
    sender_name="My App",
)
```

## Usage Examples

### Send a Plain Text Email

```python
from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator

send_notification = MailtrapSendEmailOperator(
    task_id="send_notification",
    to="user@example.com",
    subject="Task Completed",
    text="Your workflow has completed successfully.",
    sender="notifications@yourdomain.com",
)
```

### Send an HTML Email

```python
send_report = MailtrapSendEmailOperator(
    task_id="send_report",
    to="team@example.com",
    subject="Daily Report",
    html="""
    <html>
        <body>
            <h1>Daily Report</h1>
            <p>Here is your daily summary...</p>
        </body>
    </html>
    """,
    sender="reports@yourdomain.com",
    sender_name="Report Bot",
    category="daily-reports",  # For Mailtrap analytics
)
```

### Send to Multiple Recipients

```python
send_to_team = MailtrapSendEmailOperator(
    task_id="notify_team",
    to=["alice@example.com", "bob@example.com"],
    subject="Team Update",
    text="Important update for the team.",
    sender="noreply@yourdomain.com",
)
```

### Use Templated Fields

All parameters are templatable, so you can use Jinja templates:

```python
send_dynamic_email = MailtrapSendEmailOperator(
    task_id="send_dynamic_email",
    to="{{ var.value.recipient_email }}",
    subject="Report for {{ ds }}",
    text="Data processed: {{ ti.xcom_pull(task_ids='process_data') }}",
    sender="{{ var.value.sender_email }}",
)
```

## Operator Parameters

| Parameter          | Type               | Required | Description                                   |
| ------------------ | ------------------ | -------- | --------------------------------------------- |
| `to`               | `str \| list[str]` | ✅       | Recipient email address(es)                   |
| `subject`          | `str`              | ✅       | Email subject line                            |
| `text`             | `str`              | ⚠️       | Plain text body (required if no `html`)       |
| `html`             | `str`              | ⚠️       | HTML body (required if no `text`)             |
| `sender`           | `str`              | ⚠️       | Sender email (falls back to connection extra) |
| `sender_name`      | `str`              | ❌       | Display name for sender                       |
| `category`         | `str`              | ❌       | Category for Mailtrap analytics               |
| `mailtrap_conn_id` | `str`              | ❌       | Connection ID (default: `mailtrap_default`)   |

## Using the Hook Directly

For more advanced use cases, you can use the hook directly:

```python
from mailtrap_provider.hooks.mailtrap import MailtrapHook

# Simple usage with the helper method
hook = MailtrapHook()
response = hook.send_email(
    sender="sender@example.com",
    to="recipient@example.com",
    subject="Hello",
    text="Hello from Airflow!",
)

# Advanced usage with raw client
client = hook.get_conn()  # Returns mailtrap.MailtrapClient
# Use client directly for advanced features
```

## Connection Extras

You can store default sender information in the connection extras:

```json
{
  "sender": "noreply@yourdomain.com",
  "sender_name": "Your Application"
}
```

When `sender` is not provided to the operator, it will use the value from connection extras.

## Development

### Setup Development Environment

```bash
# Install Astro CLI (macOS)
brew install astro

# Setup dev environment
./scripts/setup-dev.sh

# Start local Airflow
cd dev && astro dev start
```

Access Airflow UI at http://localhost:8080 (user: `admin`, pass: `admin`)

> **Note:** The setup script enables `AIRFLOW__CORE__TEST_CONNECTION=Enabled` so the "Test" button works in the connection form. This is disabled by default in Airflow for security.

### After Code Changes

```bash
./scripts/sync-provider.sh
```

### Run Tests

```bash
pip install pytest requests-mock
pytest tests/ -v
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Links

- [Mailtrap Documentation](https://mailtrap.io/docs)
- [Mailtrap Python SDK](https://github.com/railsware/mailtrap-python)
- [Apache Airflow](https://airflow.apache.org/)
