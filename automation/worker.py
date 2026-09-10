"""Notion approval queue -> one branded social image -> private Drive folder.

Run one worker per state directory. Secrets are read only from environment.
"""
import argparse
import html
import json
import os
import re
from pathlib import Path
import sqlite3
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def request(url, *, token=None, data=None, method=None, headers=None):
    headers = dict(headers or {})
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if isinstance(data, dict):
        data = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    # Do not automatically retry writes: an upload may have succeeded before timeout.
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'HTTP {exc.code} from {urllib.parse.urlsplit(url).hostname}') from None


def text(prop):
    kind = prop.get('type')
    value = prop.get(kind)
    if kind in ('title', 'rich_text'):
        return ''.join(x.get('plain_text', x.get('text', {}).get('content', '')) for x in value or [])
    if kind in ('select', 'status'):
        return (value or {}).get('name', '')
    if kind == 'multi_select':
        return [x['name'] for x in value or []]
    return value


def normalize(page):
    return {**{k: text(v) for k, v in page['properties'].items()}, 'id': page['id']}


def eligible(row, cfg):
    return row.get(cfg['status_property']) == cfg['ready_value'] and row.get('DK อนุมัติ') is True and not row.get('เผยแพร่แล้ว')


SOLAR_ART = '''<svg viewBox="0 0 900 250" xmlns="http://www.w3.org/2000/svg"
 role="img" aria-label="Solar PV industrial illustration" style="display:block;width:100%;height:100%">
 <g fill="none" stroke="currentColor" stroke-width="3" opacity=".8">
 <path d="M80 185L165 60H645L730 185Z M108 145H704 M137 103H675
 M260 60L224 185 M355 60L342 185 M450 60L460 185 M545 60L578 185
 M205 185V225 M605 185V225 M165 225H645"/>
 <circle cx="765" cy="54" r="25"/><path d="M765 10V0 M765 98V110 M721 54H708 M809 54H823
 M734 23L724 13 M796 85L806 95 M796 23L806 13 M734 85L724 95"/>
 </g></svg>'''


def build_job(row, ratio):
    if ratio not in ('4:5', '1:1', '9:16', '3:4', '16:9'):
        raise ValueError(f'Unsupported ratio: {ratio}')
    title = (row.get('ข้อความบนภาพ') or row.get('ชื่อคอนเทนต์') or '').strip()
    summary = (row.get('สรุปภาษาไทย') or '').strip()
    if not title or not summary:
        raise ValueError('ชื่อคอนเทนต์/ข้อความบนภาพ and สรุปภาษาไทย are required')
    if len(title) > 120:
        raise ValueError('ข้อความบนภาพ exceeds 120 characters; shorten it in Notion for a single social image')
    esc = lambda s: html.escape(str(s)).replace('\n', '<br>')
    category = ' · '.join((row.get('หมวดข่าว') or [])[:2]) or '24sEnergy'
    templates = {t['id']: t for t in json.loads((ROOT / 'builder/templates.json').read_text('utf-8'))['templates']}
    lines = [line.strip() for line in summary.splitlines() if line.strip()]
    is_list = 2 <= len(lines) <= 3 and len(summary) <= 140 and all(
        re.match(r'^(?:\d+[.)]|[-•])\s+', line) for line in lines)
    template = 'h8' if is_list else 'm5' if row.get('ประเภท') == 'ข่าว' else 'h1'
    base = json.loads(json.dumps(templates[template]))
    base['classes'] = [] if template == 'm5' else ['dark']
    content = [{'type': 'eyebrow', 'text': esc(category)}, {'type': 'rule'},
               {'type': 'head', 'size': 'sm' if len(title) > 64 else '', 'text': esc(title)}]
    # Include only a complete short summary; long summaries remain intact in caption.txt.
    if is_list:
        content.append({'type': 'checklist', 'items': [esc(re.sub(r'^(?:\d+[.)]|[-•])\s+', '', line)) for line in lines]})
    elif len(summary) <= 140 and summary != title:
        content.append({'type': 'body', 'size': 'sm', 'text': esc(summary)})
    guardrails = (row.get('Factual Guardrails') or '').strip()
    if len(guardrails) > 120:
        raise ValueError('Factual Guardrails exceeds 120 characters; prepare a concise qualified headline before rendering')
    if guardrails:
        content.append({'type': 'body', 'size': 'sm', 'text': esc(guardrails)})
    content += [{'type': 'spacer'}, {'type': 'body', 'text': SOLAR_ART,
                 'style': 'height:200px;flex-shrink:0;margin:32px 0;color:inherit'}]
    if row.get('แหล่งข่าว'):
        content.append({'type': 'source', 'text': 'ที่มา: ' + esc(row['แหล่งข่าว'])})
    content.append({'type': 'foot', 'right': '24senergy.co.th'})
    base['blocks'] = content
    return {'ratio': ratio, 'slides': [{'name': 'social-post', 'templateData': base, 'inspiredBy': template}]}


class Notion:
    def __init__(self, cfg):
        self.cfg = cfg
        self.token = os.environ['NOTION_TOKEN']

    def call(self, path, data=None):
        return request('https://api.notion.com/v1/' + path, token=self.token, data=data,
                       headers={'Notion-Version': '2025-09-03'})

    def pages(self):
        cursor = None
        while True:
            data = {'page_size': 100}
            if cursor:
                data['start_cursor'] = cursor
            result = self.call(f'data_sources/{self.cfg["data_source_id"]}/query', data)
            yield from result['results']
            if not result.get('has_more'):
                break
            cursor = result['next_cursor']

    def page(self, page_id):
        return normalize(self.call('pages/' + page_id))


class Drive:
    def __init__(self):
        self.token = None
        self.expires = 0

    def auth(self):
        if time.time() >= self.expires:
            data = urllib.parse.urlencode({
                'client_id': os.environ['GOOGLE_CLIENT_ID'],
                'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
                'refresh_token': os.environ['GOOGLE_REFRESH_TOKEN'],
                'grant_type': 'refresh_token'}).encode()
            result = request('https://oauth2.googleapis.com/token', data=data,
                             headers={'Content-Type': 'application/x-www-form-urlencoded'})
            self.token = result['access_token']
            self.expires = time.time() + result['expires_in'] - 60
        return self.token

    def call(self, path, **kwargs):
        return request('https://www.googleapis.com/drive/v3/' + path, token=self.auth(), **kwargs)

    def generate_id(self):
        return self.call('files/generateIds?count=1&space=drive&type=files')['ids'][0]

    def exists(self, file_id):
        try:
            result = self.call(f'files/{file_id}?fields=id,trashed&supportsAllDrives=true')
            if result.get('trashed'):
                raise RuntimeError('Destination was trashed; restore it before retrying')
            return True
        except RuntimeError as exc:
            if str(exc).startswith('HTTP 404 '):
                return False
            raise

    def folder(self, file_id, parent, name):
        if not self.exists(file_id):
            self.call('files?supportsAllDrives=true', data={'id': file_id, 'name': name,
                      'parents': [parent], 'mimeType': 'application/vnd.google-apps.folder'})

    def upload(self, file_id, parent, file):
        if self.exists(file_id):
            return
        mime = 'image/png' if file.suffix == '.png' else 'text/plain'
        boundary = 'socialsystem_' + uuid.uuid4().hex
        metadata = json.dumps({'id': file_id, 'name': file.name, 'parents': [parent]}).encode()
        body = (f'--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n'.encode() +
                metadata + f'\r\n--{boundary}\r\nContent-Type: {mime}\r\n\r\n'.encode() +
                file.read_bytes() + f'\r\n--{boundary}--\r\n'.encode())
        request('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true',
                token=self.auth(), data=body, headers={'Content-Type': 'multipart/related; boundary=' + boundary})


def run(cfg, state, once=False):
    state.mkdir(parents=True, exist_ok=True)
    # SQLite exclusive transaction prevents two workers from spending/rendering concurrently.
    lock = sqlite3.connect(state / 'worker.lock.sqlite', timeout=1)
    lock.execute('CREATE TABLE IF NOT EXISTS lock (id INTEGER)')
    lock.commit()
    lock.execute('BEGIN EXCLUSIVE')
    try:
        return run_locked(cfg, state, once)
    finally:
        lock.rollback()
        lock.close()


def run_locked(cfg, state, once):
    notion, drive = Notion(cfg), Drive()
    cloud_state_id = os.environ.get('DRIVE_STATE_FILE_ID')
    db_path = state / 'jobs.json'
    # Cloud state is authoritative; never fall back to empty/local state on read failure.
    db = drive.call(f'files/{cloud_state_id}?alt=media&supportsAllDrives=true') if cloud_state_id else (
        json.loads(db_path.read_text('utf-8')) if db_path.exists() else {})
    if not isinstance(db, dict):
        raise ValueError('Invalid state file')
    def save():
        temp = db_path.with_suffix('.tmp')
        temp.write_text(json.dumps(db, ensure_ascii=False, indent=2), 'utf-8')
        temp.replace(db_path)
        if cloud_state_id:
            request(f'https://www.googleapis.com/upload/drive/v3/files/{cloud_state_id}?uploadType=media&supportsAllDrives=true',
                    token=drive.auth(), data=json.dumps(db).encode(), method='PATCH',
                    headers={'Content-Type': 'application/json'})
    def resource(job, key):
        if key not in job:
            job[key] = drive.generate_id()
            save()  # Persist preallocated ID before any upload, allowing safe crash recovery.
        return job[key]
    while True:
        failed = False
        try:
            for page in notion.pages():
                row = normalize(page)
                if not eligible(row, cfg):
                    continue
                key = row['id']  # Each approved page is rendered once; new version = duplicate page.
                if db.get(key, {}).get('done'):
                    continue
                try:
                    record = db.setdefault(key, {'row': row})
                    save()
                    row = record['row']  # Resume the same immutable content snapshot after a failure.
                    destination = state / 'outputs' / key
                    destination.mkdir(parents=True, exist_ok=True)
                    # One topic = exactly one image. Prefer 4:5 when several ratios are selected.
                    selected = row.get('สัดส่วนภาพ') or ['4:5']
                    ratios = ['4:5' if '4:5' in selected else selected[0]]
                    files = []
                    for ratio in ratios:
                        target = destination / ratio.replace(':', 'x')
                        target.mkdir(exist_ok=True)
                        job = build_job(row, ratio)
                        job_file = target / 'job.json'
                        job_file.write_text(json.dumps(job, ensure_ascii=False), 'utf-8')
                        result = subprocess.run(['node', str(HERE / 'render.mjs'), str(job_file), str(target)],
                                                check=True, capture_output=True, text=True, encoding='utf-8', timeout=180)
                        report = json.loads(result.stdout)
                        if report['pageErrors'] or any(s['overflow'] for s in report['slides']):
                            raise ValueError('Render validation failed; no files uploaded')
                        files.extend(target / slide['file'] for slide in report['slides'])
                    caption = destination / 'caption.txt'
                    caption.write_text('\n\n'.join(str(row.get(k) or '') for k in
                        ('ร่างแคปชัน', 'สรุปภาษาไทย', 'Factual Guardrails', 'CTA', 'ลิงก์ข่าวต้นฉบับ')), 'utf-8')
                    files.append(caption)
                    if not eligible(notion.page(key), cfg):
                        continue  # Approval withdrawn during rendering.
                    parent = resource(record, 'folder_id')
                    drive.folder(parent, cfg['drive_folder_id'], (row.get('ชื่อคอนเทนต์') or key)[:150])
                    for file in files:
                        file_key = str(file.relative_to(destination))
                        folder = parent
                        if file.suffix == '.png':
                            folder = resource(record, 'ratio:' + file.parent.name)
                            drive.folder(folder, parent, file.parent.name)
                        drive.upload(resource(record, 'file:' + file_key), folder, file)
                    record['done'] = True
                    save()
                    print(json.dumps({'page': key, 'done': True, 'folder_id': parent}), flush=True)
                except Exception as exc:
                    failed = True
                    print(json.dumps({'page': key, 'error': str(exc)}, ensure_ascii=False), flush=True)
        except Exception as exc:
            failed = True
            print(json.dumps({'error': str(exc)}), flush=True)
        if once:
            if failed:
                raise SystemExit(1)
            return
        time.sleep(max(15, cfg.get('poll_seconds', 60)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=HERE / 'worker.config.json')
    parser.add_argument('--state', type=Path, default=HERE / '.runtime')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--init-cloud-state', action='store_true')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text('utf-8'))
    if args.init_cloud_state:
        drive = Drive()
        args.state.mkdir(parents=True, exist_ok=True)
        seed = args.state / 'socialsystem-state.json'
        seed.write_text('{}', 'utf-8')
        file_id = drive.generate_id()
        drive.upload(file_id, cfg['drive_folder_id'], seed)
        print('DRIVE_STATE_FILE_ID=' + file_id)
    else:
        run(cfg, args.state.resolve(), args.once)
