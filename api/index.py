from flask import Flask, request, jsonify
import requests
import html
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- API KEY AUTHENTICATION ---
def is_valid_key(user_key):
    if user_key == "YDAIoYzubTQCsxlG": return True
    try:
        file_path = os.path.join(os.getcwd(), 'apikey.txt')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                allowed_keys = [line.strip() for line in f.readlines() if line.strip()]
            return user_key in allowed_keys
    except: pass
    return False

@app.route('/insta', methods=['GET'])
def insta_downloader():
    insta_url = request.args.get('url')
    api_key = request.args.get('key')

    if not api_key or not is_valid_key(api_key):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 403

    if not insta_url:
        return jsonify({"status": "error", "message": "URL is required"}), 400

    try:
        insta_url = insta_url.strip()
        links_list = []
        mode = ""

        # --- STORY DOWNLOAD LOGIC (Indown Simulation) ---
        if "/stories/" in insta_url or "ig_story_item" in insta_url:
            mode = "story"
            session = requests.Session()
            
            # Browser headers set karna zaroori hai
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://indown.io/insta-stories-download"
            }
            
            # Step 1: Initial Page Load (Cookies ke liye)
            main_res = session.get("https://indown.io/insta-stories-download", headers=headers)
            soup_main = BeautifulSoup(main_res.text, "html.parser")
            
            # Step 2: Tokens ko Safety ke saath nikalna
            csrf_token = ""
            referer_val = ""
            
            token_tag = soup_main.find("input", {"name": "_token"})
            referer_tag = soup_main.find("input", {"name": "referer"})
            
            if token_tag and referer_tag:
                csrf_token = token_tag.get("value")
                referer_val = referer_tag.get("value")
            else:
                # Agar Indown block kare, toh alternate method (Reels downloader) try karna
                return jsonify({"status": "error", "message": "InDown Security Block. Please try again in 5 minutes."}), 503
            
            # Step 3: Story Data Fetch (POST)
            post_data = {
                "link": insta_url,
                "referer": referer_val,
                "_token": csrf_token
            }
            
            headers.update({"X-Requested-With": "XMLHttpRequest"})
            post_res = session.post("https://indown.io/download", data=post_data, headers=headers)
            soup_res = BeautifulSoup(post_res.text, "html.parser")
            
            # Download Buttons nikalna
            for a in soup_res.find_all('a', href=True):
                href = a['href']
                text = a.text.lower()
                if "server" in text or "download" in text:
                    if "scontent" in href or "cdn" in href:
                        if href not in links_list:
                            links_list.append(href)

        # --- REEL/POST LOGIC (SnapDownloader) ---
        else:
            mode = "video" if "/reel/" in insta_url else "photo"
            target_site = "https://snapdownloader.com/tools/instagram-reels-downloader/download?url=" if mode == "video" else "https://snapdownloader.com/tools/instagram-photo-downloader/download?url="
            target = target_site + requests.utils.quote(insta_url, safe="")
            
            r = requests.get(target, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            for btn in soup.find_all('a', class_='btn-download'):
                href = html.unescape(btn.get('href', ''))
                btn_text = btn.text.strip()
                if "/v/t51.2885-19/" in href: continue
                if mode == "video" and (".mp4" in href or "video" in btn_text.lower()):
                    if href not in links_list: links_list.append(href)
                elif mode == "photo" and ("1080" in btn_text or "image" in btn_text.lower()):
                    if href not in links_list: links_list.append(href)

        if links_list:
            return jsonify({
                "status": "success",
                "type": mode,
                "total_items": len(links_list),
                "links": links_list,
                "credits": {"api_by": "@Configexe", "join": "@Teamexemods"}
            })
        else:
            return jsonify({"status": "error", "message": "Links not found. Content may be private or InDown limit reached."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": f"Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run()
            
