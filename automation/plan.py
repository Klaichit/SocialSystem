#!/usr/bin/env python3
"""แปลงแถวจาก Notion Content Hub เป็นโครง job.json ให้ render.mjs

    python3 automation/plan.py rows.json outputs/

rows.json = ผลลัพธ์ดิบจาก notion-query-data-sources (คีย์เป็นชื่อพร็อพเพอร์ตี้ไทย)

ตัวนี้ทำแค่ "โครง" — เลือกชุดเทมเพลตตามประเภท แล้วดูดข้อความเท่าที่ดูดได้
คนที่รันรอบเช้าต้องอ่านแล้วเกลาข้อความเองก่อนเรนเดอร์ ดู MORNING.md
"""
import json, re, sys, unicodedata
from pathlib import Path

# ชุดสไลด์ต่อประเภท — ทุกชุดจบด้วย CTA เสมอ
PLANS = {
    "ข่าว":       ["h1", "m5", "h8", "m1", "m6"],
    "ให้ความรู้":  ["h1", "m2", "h12", "h8", "m6"],
    "สินค้า":     ["h1", "m2", "h8", "m3", "m6"],
    "โปรโมชัน":   ["h1", "m2", "h8", "m6"],
}
DEFAULT_PLAN = ["h1", "m2", "h8", "m6"]

# ลำดับบล็อกที่ต้องเติมข้อความในแต่ละเทมเพลต (index อ้างจาก builder/templates.json)
SLOTS = {
    "h1":  {"eyebrow": 0, "head": 2, "foot": 4},
    "m1":  {"pill": 0, "head": 1, "body": 2},
    "m2":  {"eyebrow": 0, "head": 2, "body": 3},
    "m3":  {"stat": 1},
    "m5":  {"meta": 0, "head": 2, "body": 3, "source": 5},
    "m6":  {"head": 0, "body": 1, "pill": 3},
    "h8":  {"eyebrow": 0, "head": 2, "checklist": 3},
    "h12": {"eyebrow": 0, "head": 1, "dots": 2},
}

TH_MONTH = "ม.ค. ก.พ. มี.ค. เม.ย. พ.ค. มิ.ย. ก.ค. ส.ค. ก.ย. ต.ค. พ.ย. ธ.ค.".split()

def jlist(v):
    """multi_select เก็บมาเป็นสตริง JSON"""
    if not v:
        return []
    try:
        out = json.loads(v)
        return out if isinstance(out, list) else [v]
    except (ValueError, TypeError):
        return [v]

def thai_month(iso):
    """2026-09-19 -> ก.ย. 2569"""
    m = re.match(r"(\d{4})-(\d{2})", iso or "")
    if not m:
        return ""
    return f"{TH_MONTH[int(m.group(2)) - 1]} {int(m.group(1)) + 543}"

def safe(name, limit=52):
    """ชื่อโฟลเดอร์/ไฟล์ที่ Windows กับ Drive รับได้

    หัวข้อใน Notion ยาวและมักมีท่อน — ขยายความต่อท้าย ตัดทิ้งได้
    ที่เหลือตัดที่ช่องว่าง ไม่ตัดกลางคำ"""
    name = unicodedata.normalize("NFC", name)
    name = re.split(r"\s+[—–-]\s+", name)[0]
    name = re.sub(r'[\\/:*?"<>|]', "-", name).strip(" .")
    if len(name) > limit:
        name = name[:limit].rsplit(" ", 1)[0] or name[:limit]
    return name.strip(" .")

def numbered(text):
    """ดึงบรรทัดที่ขึ้นต้นด้วยเลขข้อออกมาเป็นลิสต์"""
    return [re.sub(r"^\s*\d+[.)]\s*", "", l).strip()
            for l in (text or "").splitlines()
            if re.match(r"^\s*\d+[.)]\s", l)]

def first_sentence(text, limit=60):
    """ประโยคแรกไว้ทำพาดหัวรอง — ยาวเกินก็ตัดที่ช่องว่าง"""
    s = re.split(r"(?<=[.!?])\s|\n", (text or "").strip())[0].strip()
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(" ", 1)[0]
    return (cut or s[:limit]).strip()

def build(row):
    title    = (row.get("ชื่อคอนเทนต์") or "ไม่มีชื่อ").strip()
    kind     = (row.get("ประเภท") or "").strip()
    cats     = jlist(row.get("หมวดข่าว"))
    ratios   = jlist(row.get("สัดส่วนภาพ")) or ["4:5"]
    pubdate  = (row.get("pubdate") or row.get("date:กำหนดเผยแพร่:start") or "")[:10]
    summary  = row.get("สรุปภาษาไทย") or ""
    caption  = row.get("ร่างแคปชัน") or ""
    cover    = row.get("ข้อความบนภาพ") or title
    cta      = row.get("CTA") or "ทักแชทมาที่เพจ 24sEnergy ได้เลย"
    source   = row.get("แหล่งข่าว") or ""
    steps    = numbered(caption)

    eyebrow = " · ".join(cats[:2]) if cats else kind
    slides, seen = [], set()
    for tpl in PLANS.get(kind, DEFAULT_PLAN):
        s = SLOTS.get(tpl, {})
        b = {}
        if tpl == "h1":
            b = {s["eyebrow"]: {"text": eyebrow},
                 s["head"]: {"text": cover.replace("\n", "<br>")},
                 s["foot"]: {"right": "ปัดต่อ →"}}
            name = "ปก"
        elif tpl == "m5":
            b = {s["meta"]: {"pill": kind or "ข่าว", "date": thai_month(pubdate)},
                 s["head"]: {"text": safe(title, 46), "size": "sm"},
                 s["body"]: {"text": summary, "size": "sm"}}
            if source:
                b[s["source"]] = {"text": f"ที่มา: {source}"}
            name = "ข่าว"
        elif tpl == "m2":
            b = {s["eyebrow"]: {"text": eyebrow},
                 s["head"]: {"text": safe(title, 46), "size": "sm"},
                 s["body"]: {"text": summary, "size": "sm"}}
            name = "เนื้อหา"
        elif tpl in ("h8", "h12"):
            items = steps[:3] if tpl == "h12" else steps[:4]
            if not items:
                continue  # ไม่มีข้อให้ลิสต์ ก็ไม่ต้องมีสไลด์นี้
            key = "dots" if tpl == "h12" else "checklist"
            b = {s["eyebrow"]: {"text": "สิ่งที่ต้องรู้"},
                 s["head"]: {"text": title, "size": "sm"},
                 s[key]: {"items": items}}
            name = "จุดเด่น" if tpl == "h12" else "เช็คลิสต์"
        elif tpl == "m1":
            b = {s["pill"]: {"text": "ข้อควรระวัง"},
                 s["head"]: {"text": "ตรวจก่อนตัดสินใจ"},
                 s["body"]: {"text": "", "size": "sm"}}  # ← เกลาเองในรอบเช้า
            name = "ข้อควรระวัง"
        elif tpl == "m3":
            continue  # ต้องมีตัวเลขจริงถึงจะใส่ได้ ปล่อยให้เติมเอง
        elif tpl == "m6":
            b = {s["head"]: {"text": first_sentence(cta, 42)},
                 s["body"]: {"text": cta},
                 s["pill"]: {"text": "ทักแชทได้เลย"}}
            name = "CTA"
        else:
            continue

        while name in seen:
            name += " 2"
        seen.add(name)
        slides.append({"template": tpl, "name": name,
                       "blocks": {str(k): v for k, v in b.items()}})

    folder = f"{pubdate} {safe(title)}".strip()
    return folder, {"ratio": ratios[0], "notion": row.get("url"), "title": title,
                    "slides": slides}

LEDGER = Path(__file__).parent / "state" / "done.json"

def ledger():
    """หน้า Notion ที่ทำภาพไปแล้ว — กันรอบเช้าทำซ้ำ

    เก็บฝั่งเราแทนการเขียนสถานะกลับเข้า Notion เพราะ Render Status
    บนบอร์ดหมายถึงภาพจาก ComfyUI ไม่ใช่ carousel ชุดนี้"""
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {}

def mark(url, folder, slides):
    done = ledger()
    done[url] = {"folder": folder, "slides": slides}
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(done, ensure_ascii=False, indent=2), "utf-8")

def main():
    if sys.argv[1] == "--mark":            # plan.py --mark <url> <folder> <slides>
        mark(sys.argv[2], sys.argv[3], int(sys.argv[4]))
        return
    rows = json.loads(Path(sys.argv[1]).read_text("utf-8"))
    rows = rows.get("results", rows) if isinstance(rows, dict) else rows
    out_root = Path(sys.argv[2] if len(sys.argv) > 2 else "outputs")
    done, made, skipped = ledger(), [], []
    for row in rows:
        if row.get("url") in done:
            skipped.append(row.get("ชื่อคอนเทนต์"))
            continue
        folder, job = build(row)
        d = out_root / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / "job.json").write_text(
            json.dumps(job, ensure_ascii=False, indent=2), "utf-8")
        made.append({"folder": str(d), "slides": len(job["slides"]),
                     "title": job["title"], "notion": job["notion"]})
    print(json.dumps({"made": made, "skipped": skipped},
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
