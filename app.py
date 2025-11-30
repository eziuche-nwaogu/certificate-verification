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
    print(f"\n========== /VERIFY ENDPOINT CALLED ==========")
    try:
        uuid = request.args.get("id")
        print(f"📝 UUID from query param: {uuid}")
        if not uuid:
            print("❌ No UUID provided")
            return render_template("certificate_invalid.html", message="No UUID provided")

        # Validate environment variables
        print(f"🔧 Config check: SUPABASE_URL={'set' if SUPABASE_URL else 'NOT SET'}, effective_key={'set' if effective_key else 'NOT SET'}")
        if not SUPABASE_URL or not effective_key:
            print(f"❌ Missing config")
            return render_template("certificate_invalid.html", message="Server configuration error"), 500

        # Query Supabase for the certificate record
        # Supabase Table: 'certificates' with columns: unique_id, first_name, last_name, certificate_url
        base_url = SUPABASE_URL.rstrip("/")
        query_url = f"{base_url}/rest/v1/certificates?unique_id=eq.{uuid}"
        
        print(f"� Query URL: {query_url}")
        print(f"� Auth key present: {bool(HEADERS.get('Authorization'))}")
        
        res = requests.get(query_url, headers=HEADERS, timeout=10)
        print(f"📊 HTTP Response Status: {res.status_code}")
        print(f"📦 Response Body (first 1000 chars): {res.text[:1000]}")

        if res.status_code != 200:
            print(f"❌ Non-200 response from Supabase: {res.status_code}")
            return render_template("certificate_invalid.html", message=f"Database error: {res.status_code}"), 500

        data = res.json()
        print(f"📋 Parsed JSON data: {data}")
        
        if not data or len(data) == 0:
            print(f"❌ No records found for UUID: {uuid}")
            return render_template("certificate_invalid.html", message="Certificate not found")

        record = data[0]
        print(f"✅ Record found: {record}")
        
        certificate_url = record.get("certificate_url")
        first_name = record.get("first_name", "")
        last_name = record.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        
        print(f"✅ Rendering certificate: {full_name} with URL: {certificate_url}")
        return render_template("certificate_display.html", certificate_url=certificate_url, full_name=full_name)
    
    except Exception as e:
        print(f"❌ EXCEPTION in verify_certificate: {e}")
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
