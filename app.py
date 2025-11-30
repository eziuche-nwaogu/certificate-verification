import os
from flask import Flask, request, render_template
import requests

app = Flask(__name__)

# ---------------- CONFIG ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = "certificates"
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# ---------------- VERIFY CERTIFICATE ----------------
@app.route("/verify")
def verify_certificate():
    uuid = request.args.get("id")
    if not uuid:
        return render_template("certificate_invalid.html", message="No UUID provided")

    # Query Supabase for the certificate record
    # Supabase Table: 'certificates' with columns: uuid, first_name, last_name, certificate_url
    query_url = f"{SUPABASE_URL}/rest/v1/certificates?unique_id=eq.{uuid}"
    res = requests.get(query_url, headers=HEADERS)

    if res.status_code != 200:
        return render_template("certificate_invalid.html", message="Error accessing database")

    data = res.json()
    if not data:
        return render_template("certificate_invalid.html", message="Certificate not found")

    record = data[0]
    certificate_url = record.get("certificate_url")
    full_name = f"{record.get('first_name')} {record.get('last_name')}"

    return render_template("certificate_display.html", certificate_url=certificate_url, full_name=full_name)

# ---------------- HEALTH CHECK ----------------
@app.route("/")
def home():
    return "✅ Certificate verification backend is running."

if __name__ == "__main__":
    # Use the PORT assigned by Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
