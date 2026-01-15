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
    
    # Randomizing User-Agent slightly for better success rate
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    session.headers.update({
        "User-Agent": user_agent,
        "Accept-Language": "en-US,en;q=0.9",
    })

    try:
        # Step 1: Initial request to get cookies and CSRF
        login_url = "https://www.instagram.com/accounts/login/"
        session.get(login_url, timeout=15)
        csrf_token = session.cookies.get("csrftoken")
        
        if not csrf_token:
            return jsonify({"status": "error", "message": "CSRF Token generation failed. IP might be rate-limited."}), 500

        # Step 2: Preparing AJAX Login
        login_ajax_url = "https://www.instagram.com/accounts/login/ajax/"
        
        # Time-based password encryption prefix used by Instagram
        enc_password = f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}"
        
        payload = {
            "username": user,
            "enc_password": enc_password,
            "queryParams": {},
            "optIntoOneTap": "false"
        }
        
        headers = {
            "X-CSRFToken": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": login_url,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = session.post(login_ajax_url, data=payload, headers=headers, timeout=20)
        
        # Checking if response is valid JSON
        try:
            result = response.json()
        except:
            return jsonify({"status": "error", "message": "Invalid response from Instagram. Possible IP block."}), 500

        # Step 3: Detailed Response Logic
        if result.get("authenticated") == True:
            return jsonify({
                "status": "success",
                "message": "Login Success ✅",
                "user_id": result.get("userId"),
                "credits": "@Configexe"
            })
        
        elif result.get("user") == True and result.get("authenticated") == False:
            return jsonify({
                "status": "failed",
                "message": "Incorrect Password ❌",
                "credits": "@Configexe"
            })
            
        elif "checkpoint_url" in result:
            return jsonify({
                "status": "checkpoint",
                "message": "Security Checkpoint / 2FA Required ⚠️",
                "checkpoint_url": f"https://www.instagram.com{result.get('checkpoint_url')}",
                "credits": "@Configexe"
            })
            
        elif result.get("status") == "fail":
            # Instagram often returns 'fail' for suspicious attempts even if pass is correct
            msg = result.get("message", "Incorrect Details or Request Blocked")
            return jsonify({
                "status": "failed",
                "message": f"{msg} ❌",
                "credits": "@Configexe"
            })
        
        else:
            return jsonify({
                "status": "unknown",
                "message": "Unknown Response",
                "full_response": result
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run()
    
