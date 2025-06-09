# main.py
from flask import Flask, request, jsonify
import imaplib
import email
import re

app = Flask(__name__)

@app.route('/')
def home():
    return "IMAP Verification API running!"

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    email_addr = data.get('email')
    password = data.get('password')
    result = {}

    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com')
        mail.login(email_addr, password)
        mail.select('inbox')
        typ, data = mail.search(None, 'SUBJECT "Verify your account"')
        links = []
        for num in data[0].split():
            typ, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            body = msg.get_payload(decode=True).decode(errors='ignore')
            link = re.search(r'https://yourdomain.com/\S+', body)
            if link:
                links.append(link.group(0))
        result = { "status": "ok", "links": links }
    except Exception as e:
        result = { "status": "error", "message": str(e) }
    finally:
        try: mail.logout()
        except: pass
    return jsonify(result)

if __name__ == '__main__':
    app.run()
