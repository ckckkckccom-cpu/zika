#!/usr/bin/env python3
"""開一個本機 HTTP server，俾 build_pdf.py 同 check_site.py 共用。

點解唔直接用 file://：
  - file:// 之下 woff2 字型、localStorage、<dialog> 嘅行為同真實情況唔同
  - 相對路徑喺子路徑（GitHub Pages 係 /zika/）嘅坑，file:// 試唔出嚟
所以兩邊都行真 HTTP，測到嘅嘢先至算數。
"""
import functools
import http.server
import socketserver
import threading


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    """回傳 (httpd, port)。用完記得 httpd.shutdown()。"""
    handler = functools.partial(_Quiet, directory=directory)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]
