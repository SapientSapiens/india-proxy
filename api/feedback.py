from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. API key check
        expected_key = os.environ.get('RAG_API_KEY')
        if not expected_key:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"error": "Server misconfigured: no API_KEY set"}')
            return

        provided_key = self.headers.get('X-API-Key')
        if provided_key != expected_key:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized: Get Your Own DB Service Dude!!"}')
            return

        # 2. Read and parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            senti_text = data.get('senti_text')
            pos_neg = data.get('pos_neg')
            satis_level = data.get('satis_level')
        except Exception:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Invalid JSON"}')
            return

        # 3. Validate required fields
        if not all([senti_text, pos_neg, satis_level]):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "Missing fields: Please interact with the Feedback Section controls!"}')
            return

        # 4. Insert into database
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DATABASE_HOST'),
                port=int(os.environ.get('DATABASE_PORT')),
                user=os.environ.get('DATABASE_USER'),
                password=os.environ.get('DATABASE_PASSWORD'),
                dbname=os.environ.get('DATABASE_NAME')
            )
            cur = conn.cursor()
            # Insert into the three tables
            cur.execute(
                'INSERT INTO sentiment_distribution (senti_text) VALUES (%s)',
                (senti_text,)
            )
            cur.execute(
                'INSERT INTO positive_negative (pos_neg) VALUES (%s)',
                (pos_neg,)
            )
            cur.execute(
                'INSERT INTO satisfaction_level (satis_levl) VALUES (%s)',
                (satis_level,)
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        # 5. Success response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))