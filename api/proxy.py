from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import os

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Check API key header
        expected_key = os.environ.get('RAG_API_KEY')
        if not expected_key:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Server misconfigured: no RAG_API_KEY set"}')
            return

        # Get the API key from the request header
        provided_key = self.headers.get('X-API-Key')
        if provided_key != expected_key:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized:Get Your RAG API Dude!!"}')
            return

        # 2. Read the incoming request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        request_json = json.loads(post_data)

        # 3. Forward to your internal API
       
        internal_url = os.environ.get('INTERNAL_URL')
        req = urllib.request.Request(
            internal_url,
            data=json.dumps(request_json).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(response_data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))