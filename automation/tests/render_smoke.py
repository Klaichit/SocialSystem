"""Render synthetic Thai posts in every supported ratio, without account credentials."""
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from worker import HERE, build_job

root = HERE / '.runtime' / 'smoke'
for ratio in ['4:5', '1:1', '9:16', '16:9']:
    target = root / ratio.replace(':', 'x')
    target.mkdir(parents=True, exist_ok=True)
    job = build_job({'ชื่อคอนเทนต์': 'วางแผนโซลาร์ให้เหมาะกับธุรกิจ',
                     'สรุปภาษาไทย': 'เริ่มจากข้อมูลการใช้ไฟและพื้นที่ติดตั้ง เพื่อวางแผนระบบพลังงานที่เหมาะสม',
                     'ประเภท': 'ข่าว', 'หมวดข่าว': ['Solar']}, ratio)
    path = target / 'job.json'
    path.write_text(json.dumps(job, ensure_ascii=False), 'utf-8')
    result = subprocess.run(['node', str(HERE / 'render.mjs'), str(path), str(target)],
                            check=True, capture_output=True, text=True, timeout=180)
    report = json.loads(result.stdout)
    assert len(report['slides']) == 1, report
    assert not report['pageErrors'], report
    assert not report['slides'][0]['overflow'], report
    assert (target / report['slides'][0]['file']).stat().st_size > 1000
    print(ratio, 'OK')
