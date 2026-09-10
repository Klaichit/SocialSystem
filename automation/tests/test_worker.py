import json
from pathlib import Path
import sys
import contextlib
import shutil
import uuid
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import worker

CFG = {'status_property': 'ขั้นตอน', 'ready_value': 'อนุมัติแล้ว', 'drive_folder_id': 'folder'}
ROW = {'id': 'page-one', 'ขั้นตอน': 'อนุมัติแล้ว', 'DK อนุมัติ': True,
       'ชื่อคอนเทนต์': 'พลังงานสะอาด', 'สรุปภาษาไทย': 'ข้อมูลจาก Notion เท่านั้น', 'ประเภท': 'ข่าว'}


@contextlib.contextmanager
def test_directory():
    root = (Path(worker.HERE) / '.runtime' / 'tests').resolve()
    folder = root / uuid.uuid4().hex
    folder.mkdir(parents=True)
    try:
        yield folder
    finally:
        assert folder.resolve().parent == root
        shutil.rmtree(folder)


class WorkerTests(unittest.TestCase):
    def test_approval_requires_both_and_unpublished(self):
        self.assertTrue(worker.eligible(ROW, CFG))
        for change in ({'DK อนุมัติ': False}, {'ขั้นตอน': 'พักไว้'}, {'เผยแพร่แล้ว': True}):
            self.assertFalse(worker.eligible({**ROW, **change}, CFG))

    def test_html_is_escaped_and_sample_claims_removed(self):
        job = worker.build_job({**ROW, 'สรุปภาษาไทย': '<img src=x onerror=alert(1)>'}, '4:5')
        serialized = json.dumps(job, ensure_ascii=False)
        self.assertNotIn('<img', serialized)
        self.assertIn('&lt;img', serialized)
        self.assertNotIn('30%', serialized)
        self.assertEqual(len(job['slides']), 1)
        self.assertEqual(job['slides'][0]['inspiredBy'], 'm5')
        self.assertEqual(job['slides'][-1]['templateData']['blocks'][-1]['right'], '24senergy.co.th')

    def test_list_selects_checklist_and_ratio_is_explicit(self):
        job = worker.build_job({**ROW, 'สรุปภาษาไทย': '1. สำรวจพื้นที่\n2. ตรวจสอบการใช้ไฟ'}, '16:9')
        self.assertEqual(len(job['slides']), 1)
        self.assertEqual(job['slides'][0]['inspiredBy'], 'h8')
        self.assertEqual(job['ratio'], '16:9')
        with self.assertRaises(ValueError):
            worker.build_job(ROW, '../../escape')

    def test_long_summary_still_produces_one_image_and_guardrails_are_kept(self):
        long_job = worker.build_job({**ROW, 'สรุปภาษาไทย': 'ก' * 450}, '4:5')
        self.assertEqual(len(long_job['slides']), 1)
        job = worker.build_job({**ROW, 'Factual Guardrails': 'ยังไม่เปิดลงทะเบียน'}, '4:5')
        self.assertIn('ยังไม่เปิดลงทะเบียน', json.dumps(job, ensure_ascii=False))

    def test_rich_text_and_select_normalization(self):
        self.assertEqual(worker.text({'type': 'rich_text', 'rich_text': [
            {'plain_text': 'สรุป'}, {'text': {'content': 'ไทย'}}]}), 'สรุปไทย')
        self.assertEqual(worker.text({'type': 'select', 'select': {'name': 'อนุมัติแล้ว'}}), 'อนุมัติแล้ว')

    def test_crash_after_upload_resumes_same_ids(self):
        class FakeNotion:
            def __init__(self, cfg): pass
            def pages(self): return [ROW]
            def page(self, key): return ROW
        class FakeDrive:
            counter = 0
            uploads = set()
            attempts = []
            crashed = False
            def generate_id(self):
                FakeDrive.counter += 1
                return str(FakeDrive.counter)
            def folder(self, *args): pass
            def upload(self, file_id, parent, file):
                FakeDrive.attempts.append(file_id)
                FakeDrive.uploads.add(file_id)
                if not FakeDrive.crashed:
                    FakeDrive.crashed = True
                    raise RuntimeError('response lost after upload')
        def render(args, **kwargs):
            target = Path(args[-1])
            (target / '01.png').write_bytes(b'fake png for isolated unit test')
            class Result:
                stdout = json.dumps({'pageErrors': [], 'slides': [{'file': '01.png', 'overflow': False}]})
            return Result()
        with test_directory() as folder, patch.object(worker, 'Notion', FakeNotion), \
                patch.object(worker, 'Drive', FakeDrive), patch.object(worker, 'normalize', lambda x: x), \
                patch.object(worker.subprocess, 'run', render):
            state = Path(folder)
            with self.assertRaises(SystemExit):
                worker.run(CFG, state, once=True)
            worker.run(CFG, state, once=True)
            worker.run(CFG, state, once=True)
            self.assertEqual(FakeDrive.attempts[0], FakeDrive.attempts[1])
            self.assertEqual(len(FakeDrive.uploads), 2)
            self.assertTrue(json.loads((state / 'jobs.json').read_text('utf-8'))['page-one']['done'])


if __name__ == '__main__':
    unittest.main()
