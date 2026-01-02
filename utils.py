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



def send_verification_email(receiver_email, verification_token):
    # Configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 465  # For SSL
    sender_email = os.getenv("EMAIL")
    sender_password = os.getenv("APP_PASSWORD")

    # Create the verification link (Update with your actual domain)
    verification_link = f"http://127.0.0.1:8000/verify?token={verification_token}"

    # Compose the email
    msg = EmailMessage()
    msg['Subject'] = "Verify your Email Address"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # 2. HTML Version
    html_content = f"""
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
    msg.add_alternative(html_content, subtype='html')

    # Send the email
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        print(f"Verification email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False