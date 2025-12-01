import http.server
import socketserver
import os

PORT = 8002

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

if __name__ == "__main__":
    # 确保以当前脚本所在目录（根目录）为服务器根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("-" * 40)
    print(f"🚀 根目录服务器已启动: http://localhost:{PORT}")
    print(f"👉 请访问: http://localhost:{PORT}/index_test.html")
    print("✅ 已启用 COOP/COEP 安全头 (MediaPipe 必需)")
    print("-" * 40)
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")
