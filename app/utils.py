from pwdlib import PasswordHash

import smtplib
from email.message import EmailMessage

from app.config import settings

password_hash = PasswordHash.recommended()

def hash_password(password):
    return password_hash.hash(password)


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)



SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = settings.EMAIL
SENDER_PASSWORD = settings.APP_PASSWORD


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

def send_reset_password_email(receiver_email : str, reset_token: str):
    reset_link = f"http://127.0.0.1:8000/forget_password/reset?token={reset_token}"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            
            <h2 style="color: #4A90E2; text-align:center;">Reset Your Password</h2>

            <p>We received a request to reset your password for your account on the Task Management Platform.</p>

            <p>Please click the button below to choose a new password:</p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}"
                style="background-color: #4A90E2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                Reset Password
                </a>
            </div>

            <p><strong>This link will expire in 10 minutes.</strong></p>

            <p>If the button doesn’t work, copy and paste this link into your browser:</p>

            <p style="word-break: break-all;">
                <a href="{reset_link}">{reset_link}</a>
            </p>

            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">

            <p style="font-size: 12px; color: #888;">
                If you did not request a password reset, you can safely ignore this email. 
                Your password will remain unchanged.
            </p>

        </div>
    </body>
    </html>
    """
    return send_email(to_email=receiver_email, subject="Reset you password", html_content=html)


def send_task_assignment_email(receiver_email: str, task_title: str, task_description: str, 
                                assigner_name: str, task_id: int, project_name: str = None, 
                                due_date: str = None, priority: str = None):
    """
    Send an email notification when a task is assigned to a user.
    
    Args:
        receiver_email: Email of the user being assigned the task
        task_title: Title of the task
        task_description: Description of the task
        assigner_name: Name of the user who assigned the task
        task_id: ID of the task
        project_name: Name of the project (optional)
        due_date: Due date of the task (optional)
        priority: Priority level of the task (optional)
    """
    task_link = f"http://127.0.0.1:8000/tasks/{task_id}"
    
    project_info = f"<p><strong>Project:</strong> {project_name}</p>" if project_name else ""
    due_date_info = f"<p><strong>Due Date:</strong> {due_date}</p>" if due_date else ""
    priority_badge_color = {
        "high": "#E74C3C",
        "medium": "#F39C12",
        "low": "#3498DB"
    }.get(priority.lower() if priority else "", "#95A5A6")
    priority_info = f'<span style="background-color: {priority_badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; text-transform: uppercase;">{priority}</span>' if priority else ""

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
            
            <h2 style="color: #4A90E2; text-align: center;">🎯 New Task Assigned to You</h2>

            <p>Hi there,</p>

            <p><strong>{assigner_name}</strong> has assigned a new task to you.</p>

            <div style="background-color: #f8f9fa; padding: 20px; border-left: 4px solid #4A90E2; margin: 20px 0; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #2C3E50;">{task_title}</h3>
                <p style="color: #555; margin: 10px 0;">{task_description}</p>
                {project_info}
                {due_date_info}
                <p>{priority_info}</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{task_link}"
                   style="background-color: #4A90E2; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                   View Task Details
                </a>
            </div>

            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">
                <a href="{task_link}">{task_link}</a>
            </p>

            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">

            <p style="font-size: 12px; color: #888;">
                You are receiving this email because you have been assigned a task in the Task Management System.
            </p>

        </div>
    </body>
    </html>
    """

    return send_email(
        to_email=receiver_email,
        subject=f"New Task Assigned: {task_title}",
        html_content=html
    )
