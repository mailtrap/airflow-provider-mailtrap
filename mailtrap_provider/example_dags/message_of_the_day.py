"""
Message of the Day - Advanced Integration Example

This DAG demonstrates how to integrate the Mailtrap provider with other
Airflow features to create a daily digest email:

1. Fetches an inspirational quote from an API
2. Gets current weather for a city
3. Composes a beautiful HTML email
4. Sends it via Mailtrap

Schedule: Daily at 7:00 AM (or trigger manually)

Setup:
1. Create 'mailtrap_default' connection with your API token
2. Set Airflow Variables:
   - motd_recipient: Email address to receive the message
   - motd_sender: Sender email address (must be from your verified domain)
   - motd_sender_name: Sender display name (optional, defaults to "Daily Inspiration")
   - motd_city: City for weather (optional, defaults to "New York")
"""

from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from airflow.models import Variable

from mailtrap_provider.operators.send_email import MailtrapSendEmailOperator


@dag(
    dag_id="message_of_the_day",
    description="Send a daily inspirational message with quote and weather",
    start_date=datetime(2024, 1, 1),
    schedule="0 7 * * *",  # Daily at 7:00 AM
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["mailtrap", "email", "daily", "integration"],
    doc_md=__doc__,
)
def message_of_the_day():
    """
    Daily Message of the Day workflow.

    Fetches inspirational content and sends a beautifully formatted email.
    """

    @task
    def fetch_quote() -> dict:
        """Fetch an inspirational quote from the Quotable API."""
        try:
            response = requests.get(
                "https://api.quotable.io/random",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data.get("content", "Stay positive and keep moving forward!"),
                "author": data.get("author", "Unknown"),
            }
        except Exception as e:
            # Fallback quote if API fails
            print(f"Quote API failed: {e}, using fallback")
            return {
                "content": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
            }

    @task
    def fetch_weather() -> dict:
        """Fetch current weather from wttr.in (free, no API key needed)."""
        city = Variable.get("motd_city", default_var="New York")
        try:
            response = requests.get(
                f"https://wttr.in/{city}?format=j1",
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            current = data["current_condition"][0]
            return {
                "city": city,
                "temp_c": current.get("temp_C", "?"),
                "temp_f": current.get("temp_F", "?"),
                "description": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                "humidity": current.get("humidity", "?"),
                "wind_kmph": current.get("windspeedKmph", "?"),
            }
        except Exception as e:
            print(f"Weather API failed: {e}, using fallback")
            return {
                "city": city,
                "temp_c": "N/A",
                "temp_f": "N/A",
                "description": "Weather unavailable",
                "humidity": "N/A",
                "wind_kmph": "N/A",
            }

    @task
    def compose_email(quote: dict, weather: dict) -> dict:
        """Compose the HTML email content."""
        today = datetime.now().strftime("%A, %B %d, %Y")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #22d172 0%, #1a9f5c 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">☀️ Good Morning!</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">{today}</p>
                </div>

                <!-- Quote Section -->
                <div style="padding: 30px; background-color: #fafafa; border-left: 4px solid #22d172;">
                    <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">💬 Quote of the Day</h2>
                    <blockquote style="margin: 0; padding: 0; font-style: italic; color: #555; font-size: 18px; line-height: 1.6;">
                        "{quote["content"]}"
                    </blockquote>
                    <p style="margin: 15px 0 0 0; color: #888; font-size: 14px;">— {quote["author"]}</p>
                </div>

                <!-- Weather Section -->
                <div style="padding: 30px;">
                    <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">🌤️ Weather in {weather["city"]}</h2>
                    <div style="display: flex; align-items: center;">
                        <div style="background-color: #f0f0f0; border-radius: 10px; padding: 20px; text-align: center; flex: 1;">
                            <div style="font-size: 36px; font-weight: bold; color: #22d172;">{weather["temp_c"]}°C</div>
                            <div style="color: #666; font-size: 14px;">{weather["temp_f"]}°F</div>
                            <div style="color: #333; font-size: 16px; margin-top: 10px;">{weather["description"]}</div>
                        </div>
                    </div>
                    <div style="margin-top: 15px; color: #666; font-size: 14px;">
                        💧 Humidity: {weather["humidity"]}% &nbsp;&nbsp; 💨 Wind: {weather["wind_kmph"]} km/h
                    </div>
                </div>

                <!-- Footer -->
                <div style="padding: 20px; background-color: #333; text-align: center;">
                    <p style="color: #999; margin: 0; font-size: 12px;">
                        Sent with ❤️ via Apache Airflow + Mailtrap
                    </p>
                    <p style="color: #666; margin: 10px 0 0 0; font-size: 11px;">
                        Powered by <a href="https://mailtrap.io" style="color: #22d172;">Mailtrap.io</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text = f"""
Good Morning! - {today}

QUOTE OF THE DAY
"{quote["content"]}"
— {quote["author"]}

WEATHER IN {weather["city"]}
Temperature: {weather["temp_c"]}°C / {weather["temp_f"]}°F
Conditions: {weather["description"]}
Humidity: {weather["humidity"]}%
Wind: {weather["wind_kmph"]} km/h

---
Sent via Apache Airflow + Mailtrap
        """

        return {
            "html": html,
            "text": text.strip(),
            "subject": f"☀️ Good Morning! Your Daily Inspiration - {today}",
        }

    # Define the task flow
    quote_data = fetch_quote()
    weather_data = fetch_weather()
    email_content = compose_email(quote_data, weather_data)

    # Send the email using Mailtrap
    send_email = MailtrapSendEmailOperator(
        task_id="send_daily_email",
        to="{{ var.value.motd_recipient }}",
        subject="{{ ti.xcom_pull(task_ids='compose_email')['subject'] }}",
        html="{{ ti.xcom_pull(task_ids='compose_email')['html'] }}",
        text="{{ ti.xcom_pull(task_ids='compose_email')['text'] }}",
        sender="{{ var.value.motd_sender }}",
        sender_name="{{ var.value.motd_sender_name | default('Daily Inspiration') }}",
        category="daily-digest",
    )

    # Set dependencies
    email_content >> send_email


message_of_the_day()
