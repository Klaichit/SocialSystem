"""One-time Google Desktop OAuth. Prints a consent URL, never tokens."""
import argparse
import http.server
import json
from pathlib import Path
import secrets
import urllib.parse
from worker import request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('client_json', type=Path)
    args = parser.parse_args()
    client = json.loads(args.client_json.read_text('utf-8'))['installed']
    state = secrets.token_urlsafe(32)
    result = {}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
            valid = query.get('state') == [state]
            if valid:
                result.update(query)
            self.send_response(200 if valid else 400)
            self.end_headers()
            self.wfile.write(b'You may close this tab.' if valid else b'Invalid state.')
    with http.server.HTTPServer(('127.0.0.1', 0), Handler) as server:
        server.timeout = 300
        redirect = f'http://127.0.0.1:{server.server_port}/'
        params = {'client_id': client['client_id'], 'redirect_uri': redirect,
                  'response_type': 'code', 'scope': 'https://www.googleapis.com/auth/drive',
                  'access_type': 'offline', 'prompt': 'consent', 'state': state}
        print('Open this URL in your browser:\nhttps://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params))
        server.handle_request()
    if not result.get('code'):
        raise SystemExit('Authorization cancelled, invalid, or timed out. Run again.')
    data = urllib.parse.urlencode({'client_id': client['client_id'], 'client_secret': client['client_secret'],
        'code': result['code'][0], 'redirect_uri': redirect, 'grant_type': 'authorization_code'}).encode()
    token = request('https://oauth2.googleapis.com/token', data=data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if not token.get('refresh_token'):
        raise SystemExit('No refresh token returned; repeat consent.')
    target = Path(__file__).resolve().parent / '.runtime/google-oauth.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'client_id': client['client_id'], 'client_secret': client['client_secret'],
                                 'refresh_token': token['refresh_token']}), 'utf-8')
    print('Saved credentials to .runtime/google-oauth.json (gitignored). Keep this file private.')


if __name__ == '__main__':
    main()
