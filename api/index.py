from flask import Flask, request, jsonify
import requests
import time
import os

app = Flask(__name__)

# --- API KEY AUTHENTICATION ---
def is_valid_key(user_key):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, 'apikey.txt')
        if not os.path.exists(file_path): return False
        with open(file_path, 'r') as f:
            allowed_keys = [line.strip() for line in f.readlines()]
        return user_key in allowed_keys
    except:
        return False

@app.route('/iglogin', methods=['GET'])
def ig_login():
    usex = request.args.get('user')
    pww = request.args.get('pass')
    api_key = request.args.get('key')

    # Security Check
    if not api_key or not is_valid_key(api_key):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403

    if not usex or not pww:
        return jsonify({"status": "error", "message": "User/Pass missing"}), 400

    # --- EXACT TERMUX LOGIC ---
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    })

    try:
        # Get CSRF
        session.get("https://www.instagram.com/accounts/login/", timeout=10)
        csrf_token = session.cookies.get("csrftoken")
        
        if not csrf_token:
            return jsonify({"status": "error", "message": "CSRF not found"}), 500

        # Login Data
        p = {
            "username": usex,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{pww}",
            "queryParams": {},
            "optIntoOneTap": "false"
        }
        h = {
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Send Request
        r = session.post(
            "https://www.instagram.com/accounts/login/ajax/",
            data=p,
            headers=h,
            timeout=20
        )
        
        result = r.json()

        # Final Verification (Termux logic based)
        if "userId" in result:
            return jsonify({
                "status": "success",
                "message": "Login Success ✅",
                "userId": result['userId'],
                "credits": "@Configexe"
            })
        elif result.get("status") == "fail":
            return jsonify({
                "status": "failed",
                "message": "Incorrect Details",
                "credits": "@Configexe"
            })
        elif "checkpoint_url" in result:
            # Pointing to the specific challenge link
            return jsonify({
                "status": "checkpoint",
                "message": "Security Checkpoint ⚠️ (Login from App first)",
                "url": f"https://www.instagram.com{result['checkpoint_url']}",
                "credits": "@Configexe"
            })
        else:
            return jsonify({
                "status": "unknown",
                "message": "Unknown Response",
                "full_data": result
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run()
            
