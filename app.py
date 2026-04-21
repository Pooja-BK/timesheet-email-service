import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def send_email(to_email, subject, body_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())

def base_template(content):
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        {content}
        <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">
            This is an automated notification from TimesheetPro. Please do not reply to this email.
        </p>
    </div>
    """

def get_subject_and_body(type_, name, period, reason="", app_url=""):
    review_link = f'<a href="{app_url}" style="color: #1a73e8;">Review Timesheet</a>' if app_url else ""
    request_link = f'<a href="{app_url}" style="color: #1a73e8;">Review Request</a>' if app_url else ""

    templates = {

        # ── Employee submits timesheet → Manager receives this ──
        "submitted": (
            f"Timesheet Submitted – {period}",
            base_template(f"""
                <h2 style="color:#333;">Timesheet Submitted</h2>
                <p>Hi User,</p>
                <p><strong>{name}</strong> has submitted a timesheet for <strong>{period}</strong>.</p>
                <p>✓ <strong>Action Required</strong> - Please review and approve or reject this timesheet.</p>
                <p>{review_link}</p>
            """)
        ),

        # ── Employee requests edit access → Manager receives this ──
        "edit_requested": (
            f"Edit Access Requested – {period}",
            base_template(f"""
                <h2 style="color:#333;">Edit Access Requested</h2>
                <p>Hi User,</p>
                <p><strong>{name}</strong> has requested edit access for <strong>{period}</strong>.</p>
                <p>⚠️ <strong>Action Required</strong> - Please review and approve or reject this request.</p>
                <p>Reason for Edit<br>{reason}</p>
                <p>{request_link}</p>
            """)
        ),

        # ── Manager approves timesheet → Employee receives this ──
        "approved": (
            f"Timesheet Approved – {period}",
            base_template(f"""
                <h2 style="color:#2e7d32;">Timesheet Approved</h2>
                <p>Hi {name},</p>
                <p>Your timesheet for <strong>{period}</strong> has been <strong style="color:#2e7d32;">approved</strong>.</p>
                <p>No further action is required.</p>
            """)
        ),

        # ── Manager rejects timesheet → Employee receives this ──
        "rejected": (
            f"Timesheet Rejected – {period}",
            base_template(f"""
                <h2 style="color:#c62828;">Timesheet Rejected</h2>
                <p>Hi {name},</p>
                <p>Your timesheet for <strong>{period}</strong> has been <strong style="color:#c62828;">rejected</strong>.</p>
                <p>Please review and resubmit your timesheet.</p>
                {f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""}
            """)
        ),

        # ── Manager approves edit access → Employee receives this ──
        "edit_approved": (
            f"Edit Access Approved – {period}",
            base_template(f"""
                <h2 style="color:#2e7d32;">Edit Access Approved</h2>
                <p>Hi {name},</p>
                <p>Your request to edit the timesheet for <strong>{period}</strong> has been <strong style="color:#2e7d32;">approved</strong>.</p>
                <p>You can now make changes to your timesheet.</p>
                <p>{review_link}</p>
            """)
        ),

        # ── Manager rejects edit access → Employee receives this ──
        "edit_rejected": (
            f"Edit Access Rejected – {period}",
            base_template(f"""
                <h2 style="color:#c62828;">Edit Access Rejected</h2>
                <p>Hi {name},</p>
                <p>Your request to edit the timesheet for <strong>{period}</strong> has been <strong style="color:#c62828;">rejected</strong>.</p>
                {f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""}
            """)
        ),
    }

    return templates.get(type_)

@app.route("/send-email", methods=["POST"])
def trigger_email():
    data = request.json
    to      = data.get("to")
    type_   = data.get("type")
    name    = data.get("name", "User")
    period  = data.get("period", "")
    reason  = data.get("reason", "")
    app_url = data.get("appUrl", "")

    result = get_subject_and_body(type_, name, period, reason, app_url)

    if not result:
        return jsonify({"error": "Invalid email type"}), 400

    subject, body = result

    try:
        send_email(to, subject, body)
        return jsonify({"message": "Email sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
