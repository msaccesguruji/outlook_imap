from flask import Flask, request, jsonify
import imaplib
import email
from email.header import decode_header

app = Flask(__name__)

def parse_email(msg):
    def decode_str(s):
        if not s: return ""
        parts = decode_header(s)
        return ''.join([
            t[0].decode(t[1] or 'utf-8') if isinstance(t[0], bytes) else t[0]
            for t in parts
        ])

    subject = decode_str(msg['Subject'])
    sender = decode_str(msg['From'])
    date = msg['Date']
    try:
        date = str(email.utils.parsedate_to_datetime(date))
    except:
        pass

    # Prefer HTML body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                body = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='ignore')
                break
            elif part.get_content_type() == 'text/plain' and not body:
                body = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='ignore')
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8'), errors='ignore')

    return {
        "subject": subject,
        "sender": sender,
        "date": date,
        "body": body
    }

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    email_addr = data.get('email')
    password = data.get('password')
    subject_substr = data.get('subject', '').lower()
    results = []

    try:
        mail = imaplib.IMAP4_SSL('outlook.office365.com')
        mail.login(email_addr, password)
        mail.select('inbox')
        typ, data_ids = mail.search(None, 'ALL')
        for num in data_ids[0].split():
            typ, msg_data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])
            subject = msg['Subject']
            # Partial, case-insensitive subject match
            if subject and subject_substr in subject.lower():
                results.append(parse_email(msg))
        mail.logout()
        return jsonify({"status": "ok", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/')
def home():
    return "Hotmail IMAP Search API Running!"
