# api/proxy.py

"""
Vercel proxy for the RAG backend.

Author: Siddhartha Gogoi

Purpose:
This file validates the external API key, forwards requests from the public-facing
proxy endpoint to the internal RAG API, and preserves the X-Session-ID header in
both directions so multi-turn conversation state survives the trip.

No backend surgery, no species mutation, no architectural enlightenment campaign.
Just a thin proxy doing its actual job.
"""

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
        if not internal_url:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Server misconfigured: no INTERNAL_URL set"}')
            return

        forward_headers = {
            'Content-Type': 'application/json',
        }

        # Forward incoming session id if client already has one
        session_id = self.headers.get('X-Session-ID')
        if session_id:
            forward_headers['X-Session-ID'] = session_id

        req = urllib.request.Request(
            internal_url,
            data=json.dumps(request_json).encode('utf-8'),
            headers=forward_headers,
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()

                # Capture session id returned by backend
                upstream_session_id = response.headers.get('X-Session-ID')

                self.send_response(response.status)
                self.send_header('Content-Type', 'application/json')

                # Return session id to Streamlit so it can reuse it next turn
                if upstream_session_id:
                    self.send_header('X-Session-ID', upstream_session_id)

                self.end_headers()
                self.wfile.write(response_data)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))