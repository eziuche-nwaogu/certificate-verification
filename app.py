import os
from flask import Flask, request, render_template
import requests

app = Flask(__name__)

# ---------------- CONFIG ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
BUCKET_NAME = "certificates"
# Prefer the service role key for server-side operations if available
effective_key = SUPABASE_KEY or SUPABASE_SERVICE_ROLE_KEY
HEADERS = {
    "apikey": effective_key,
    "Authorization": f"Bearer {effective_key}" if effective_key else ""
}

print(f"🔧 SUPABASE_URL={'set' if SUPABASE_URL else 'missing'}, SUPABASE_KEY={'set' if SUPABASE_KEY else 'missing'}, SUPABASE_SERVICE_ROLE_KEY={'set' if SUPABASE_SERVICE_ROLE_KEY else 'missing'})")

# ---------------- VERIFY CERTIFICATE ----------------
@app.route("/verify")
def verify_certificate():
    try:
        uuid = request.args.get("id")
        if not uuid:
            return render_template("certificate_invalid.html", message="No UUID provided")

        # Validate environment variables
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("❌ SUPABASE_URL or SUPABASE_KEY is not set")
            return render_template("certificate_invalid.html", message="Server configuration error"), 500

        # Query Supabase for the certificate record
        # Supabase Table: 'certificates' with columns: unique_id, first_name, last_name, certificate_url
        base_url = SUPABASE_URL.rstrip("/")
        query_url = f"{base_url}/rest/v1/certificates?unique_id=eq.{uuid}"
        
        print(f"🔍 DEBUG: Querying Supabase at {query_url}")
        print(f"🔍 DEBUG: Headers: apikey={'set' if HEADERS.get('apikey') else 'missing'}, Authorization={'set' if HEADERS.get('Authorization') else 'missing'}")
        
        res = requests.get(query_url, headers=HEADERS, timeout=10)
        print(f"✅ Response status: {res.status_code}")
        print(f"✅ Response body: {res.text[:500]}")

        if res.status_code != 200:
            return render_template("certificate_invalid.html", message=f"Database error: {res.status_code}"), 500

        data = res.json()
        if not data:
            return render_template("certificate_invalid.html", message="Certificate not found")

        record = data[0]
        certificate_url = record.get("certificate_url")
        first_name = record.get("first_name", "")
        last_name = record.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()

        return render_template("certificate_display.html", certificate_url=certificate_url, full_name=full_name)
    
    except Exception as e:
        print(f"❌ Error in verify_certificate: {e}")
        import traceback
        traceback.print_exc()
        return render_template("certificate_invalid.html", message=f"Server error: {str(e)}"), 500

# ---------------- HEALTH CHECK ----------------
@app.route("/")
def home():
    return "✅ Certificate verification backend is running."

if __name__ == "__main__":
    # Use the PORT assigned by Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
