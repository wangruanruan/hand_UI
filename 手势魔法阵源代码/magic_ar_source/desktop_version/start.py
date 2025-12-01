import http.server
import socketserver
import os
import urllib.request
import ssl

# ==========================================
# 🔑 关键修复：强制忽略 SSL 证书错误
ssl._create_default_https_context = ssl._create_unverified_context
# ==========================================

# 配置
PORT = 8001
DIR = "mediapipe"
FILES = [
    "hands.js",
    "hands_solution_packed_assets_loader.js",
    "hands_solution_simd_wasm_bin.js",
    "hands_solution_simd_wasm_bin.wasm",
    "hands_solution_wasm_bin.js",
    "hands_solution_wasm_bin.wasm",
    "hand_landmark_full.tflite",
    "palm_detection_full.tflite"
]
BASE_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/hands/"

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

def check_and_download():
    if not os.path.exists(DIR):
        os.makedirs(DIR)
    
    print("-" * 40)
    print("🔍 正在尝试“强力”下载缺失文件...")
    
    for file in FILES:
        path = os.path.join(DIR, file)
        download_needed = False
        
        if not os.path.exists(path):
            print(f"[❌ 缺失] {file}")
            download_needed = True
        else:
            size = os.path.getsize(path)
            if size < 1000:
                print(f"[⚠️ 损坏] {file}")
                download_needed = True
        
        if download_needed:
            print(f"   ⬇️ 正在下载 {file} ...")
            try:
                url = BASE_URL + file
                urllib.request.urlretrieve(url, path)
                print("   ✨ 下载成功！")
            except Exception as e:
                print(f"   💥 依然失败: {e}")

                # 备用下载逻辑 (专门针对 404 的文件)
                if "palm_detection_full.tflite" in file:
                    print("   🔄 尝试从 Google Storage 备用源下载...")
                    try:
                        alt_url = "https://storage.googleapis.com/mediapipe-assets/palm_detection_full.tflite"
                        urllib.request.urlretrieve(alt_url, path)
                        print("   ✨ 备用源下载成功！")
                    except Exception as e2:
                         print(f"   ❌ 备用源也失败了: {e2}")

def run_server():
    print("-" * 40)
    print(f"🚀 服务器已启动: http://localhost:{PORT}")
    print("等待你的好消息...")
    print("-" * 40)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    # 确保切换到脚本所在目录，防止服务错误的根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    check_and_download()
    run_server()
