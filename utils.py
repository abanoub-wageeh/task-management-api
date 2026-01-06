from pwdlib import PasswordHash

import smtplib
from email.message import EmailMessage

import os
from dotenv import load_dotenv

load_dotenv()

password_hash = PasswordHash.recommended()

def hash_password(password):
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)



SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.getenv("EMAIL")
SENDER_PASSWORD = os.getenv("APP_PASSWORD")


def send_email(to_email: str, subject: str, html_content: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email sending error: {e}")
        return False


def send_verification_email(receiver_email: str, verification_token: str):
    verification_link = f"http://127.0.0.1:8000/verify?token={verification_token}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            <h2 style="color: #4A90E2;">Welcome to the task managment platform!</h2>
            <p>Thank you for signing up. Please click the button below to verify your email address and activate your account:</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" 
                   style="background-color: #4A90E2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                   Verify Email Address
                </a>
            </div>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all;"><a href="{verification_link}">{verification_link}</a></p>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888;">If you didn't create an account, you can safely ignore this email.</p>
        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=receiver_email,
        subject="Verify your Email Address",
        html_content=html
    )