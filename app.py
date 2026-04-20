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

@app.route("/send-email", methods=["POST"])
def trigger_email():
    data = request.json
    to = data.get("to")
    type_ = data.get("type")
    name = data.get("name", "Employee")
    period = data.get("period", "")

    subjects = {
        "submitted": f"Timesheet Submitted – {period}",
        "approved":  f"Timesheet Approved – {period}",
        "rejected":  f"Timesheet Rejected – {period}",
    }
    bodies = {
        "submitted": f"<p>Hi {name},</p><p>Your timesheet for <b>{period}</b> has been submitted.</p>",
        "approved":  f"<p>Hi {name},</p><p>Your timesheet for <b>{period}</b> has been <b style='color:green'>approved</b>.</p>",
        "rejected":  f"<p>Hi {name},</p><p>Your timesheet for <b>{period}</b> was <b style='color:red'>rejected</b>. Please resubmit.</p>",
    }

    if type_ not in subjects:
        return jsonify({"error": "Invalid type"}), 400

    try:
        send_email(to, subjects[type_], bodies[type_])
        return jsonify({"message": "Email sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
