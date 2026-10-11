# -*- coding: utf-8 -*-
"""演示方式：只读取内置的已算好结果，不需要显卡和深度学习库。用法：python serve.py [端口]，浏览器打开 http://127.0.0.1:端口/frontend/"""
import os, sys, http.server, functools
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); port = int(sys.argv[1]) if len(sys.argv) > 1 else 8780
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
print(f"http://127.0.0.1:{port}/frontend/"); http.server.ThreadingHTTPServer(("127.0.0.1", port), h).serve_forever()
