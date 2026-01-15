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

# --- INSTAGRAM LOGIN ROUTE ---
@app.route('/iglogin', methods=['GET'])
def ig_login():
    user = request.args.get('user')
    password = request.args.get('pass')
    api_key = request.args.get('key')

    # Security Check
    if not api_key or not is_valid_key(api_key):
        return jsonify({
            "status": "error", 
            "message": "Invalid or Missing API Key",
            "credits": "@Teamexemods"
        }), 403

    if not user or not password:
        return jsonify({"status": "error", "message": "Username and Password are required"}), 400

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    })

    try:
        # Step 1: Get CSRF Token
        session.get("https://www.instagram.com/accounts/login/", timeout=15)
        csrf_token = session.cookies.get("csrftoken")
        
        if not csrf_token:
            return jsonify({"status": "error", "message": "Unable to fetch CSRF token"}), 500

        # Step 2: Login Request
        payload = {
            "username": user,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}",
            "queryParams": {},
            "optIntoOneTap": "false"
        }
        
        headers = {
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/accounts/login/",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = session.post(
            "https://www.instagram.com/accounts/login/ajax/",
            data=payload,
            headers=headers,
            timeout=20
        )
        
        result = response.json()

        # Step 3: Response Handling
        if result.get("authenticated") == True or "userId" in result:
            return jsonify({
                "status": "success",
                "message": "Login Success ✅",
                "user_id": result.get("userId"),
                "credits": "@Configexe"
            })
        elif result.get("status") == "fail":
            return jsonify({
                "status": "failed",
                "message": "Incorrect Details ❌",
                "credits": "@Configexe"
            })
        elif "checkpoint_url" in result:
             return jsonify({
                "status": "checkpoint",
                "message": "Verification Required (2FA/Email) ⚠️",
                "checkpoint_url": result.get("checkpoint_url")
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Unknown Response or Blocked IP",
                "raw": result
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run()
      
