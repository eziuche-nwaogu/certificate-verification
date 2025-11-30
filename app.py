import os
import psycopg2
from flask import Flask, request, render_template

app = Flask(__name__)

# Environment variables injected by Railway
SUPABASE_URL = os.environ.get("SUPABASE_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")   # full Postgres connection string

# ---------------- DB CONNECTION ----------------
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print("❌ Database connection error:", e)
        return None


# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return "<h2>Certificate Verification Server Running ✔</h2>"


@app.route("/verify")
def verify_certificate():
    uuid = request.args.get("id")

    if not uuid:
        return render_template("certificate_invalid.html", reason="No certificate ID supplied."), 400

    conn = get_db_connection()
    if not conn:
        return render_template("certificate_invalid.html", reason="Database connection failed."), 500

    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT first_name, last_name, email, certificate_url
            FROM certificates
            WHERE unique_id = %s
            LIMIT 1
        """, (uuid,))

        row = cur.fetchone()

        if not row:
            return render_template("certificate_invalid.html", reason="Certificate not found."), 404

        first_name, last_name, email, certificate_url = row

        return render_template(
            "certificate_display.html",
            full_name=f"{first_name} {last_name}",
            email=email,
            certificate_url=certificate_url,
            uuid=uuid
        )

    except Exception as e:
        print("❌ Error during verification:", e)
        return render_template("certificate_invalid.html"), 500
    finally:
        cur.close()
        conn.close()


# ---------------- RAILWAY ENTRY POINT ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
