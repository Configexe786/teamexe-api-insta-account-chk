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
            
            # Step 1: Token aur Referer lena (InDown ki security bypass karne ke liye)
            main_res = session.get("https://indown.io/insta-stories-download")
            soup_main = BeautifulSoup(main_res.text, "html.parser")
            
            # Error Fix: Check kar rahe hain ki tokens mil rahe hain ya nahi
            try:
                token_input = soup_main.find("input", {"name": "_token"})
                referer_input = soup_main.find("input", {"name": "referer"})
                
                if not token_input or not referer_input:
                    return jsonify({"status": "error", "message": "Failed to bypass security tokens"}), 500
                
                csrf_token = token_input["value"]
                referer = referer_input["value"]
            except Exception:
                return jsonify({"status": "error", "message": "InDown security tokens not found"}), 500
            
            # Step 2: Form Submit karna (Jaise Search button dabaya ho)
            post_data = {
                "link": insta_url,
                "referer": referer,
                "_token": csrf_token
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Referer": "https://indown.io/insta-stories-download",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            post_res = session.post("https://indown.io/download", data=post_data, headers=headers)
            soup_res = BeautifulSoup(post_res.text, "html.parser")
            
            # Step 3: Server 1 aur Server 2 ke buttons dhoondna
            for a in soup_res.find_all('a', href=True):
                href = a['href']
                btn_text = a.get_text(strip=True).lower()
                
                # Screenshot ke mutabik 'Download Server 1' dhoond rahe hain
                if "server" in btn_text or "download" in btn_text:
                    if "scontent" in href or "cdn" in href:
                        if href not in links_list:
                            links_list.append(href)

        # --- REEL/POST LOGIC (SnapDownloader) ---
        else:
            mode = "video" if "/reel/" in insta_url else "photo"
            base = "https://snapdownloader.com/tools/instagram-reels-downloader/download?url=" if mode == "video" else "https://snapdownloader.com/tools/instagram-photo-downloader/download?url="
            target = base + requests.utils.quote(insta_url, safe="")
            
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
            r = requests.get(target, headers=headers, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")

            for btn in soup.find_all('a', class_='btn-download'):
                href = html.unescape(btn.get('href', ''))
                text = btn.get_text(strip=True)
                if "/v/t51.2885-19/" in href: continue
                
                if mode == "video":
                    if ".mp4" in href or "video" in text.lower():
                        if href not in links_list: links_list.append(href)
                else:
                    if "1080" in text or "image" in text.lower():
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
            return jsonify({"status": "error", "message": "Could not find links. Make sure the story is public and not expired."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": f"System Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run()
    
