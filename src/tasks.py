import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "cinema_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_track_started=True,
    result_persistent=True,
    timezone="Europe/Kyiv",
    enable_utc=True,
)


@celery_app.task(name="src.tasks.send_payment_success_email")
def send_payment_success_email(email_to: str, order_id: int):
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    msg = MIMEMultipart()
    msg["From"] = "noreply@online-cinema.com"
    msg["To"] = email_to
    msg["Subject"] = f"Receipt for Order #{order_id}"

    html = f"""
    <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
        <h1 style="color: #4CAF50;">Payment Successful!</h1>
        <p>Thank you for your purchase at Online Cinema.</p>
        <p>Your order <b>#{order_id}</b> has been successfully paid. The movies are now available in your account.</p>
        <hr>
        <p style="font-size: 12px; color: gray;">This is an automated email, please do not reply.</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        return f"Email sent successfully to {email_to}!"
    except Exception as e:
        print(f"SMTP Error: {e}")
        raise e
