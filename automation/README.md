# automation

ระบบตรวจสถานะ Notion และอัปโหลด PNG เข้า Drive โดยตรง: ดู [WORKER.md](WORKER.md)
ใช้ `worker.py` กับ `worker.config.json` สำหรับระบบใหม่ที่ทำงานต่อเนื่อง

ตัวเรนเดอร์แบบไม่ต้องเปิดเบราว์เซอร์ สำหรับรอบทำภาพอัตโนมัติ

## render.mjs

```
node automation/render.mjs <job.json> <outdir>
```

โหลด `builder/index.html` ใน headless Chromium แล้วเรียก `renderTemplate()` กับ CSS ชุดเดิม
ของเครื่องมือตรง ๆ — ไม่มีสำเนา layout แยก แก้เทมเพลตที่เดียวมีผลทั้งสองทาง

ถ่ายภาพด้วย screenshot ของ Playwright ไม่ใช่ html2canvas เพราะ
(ก) คมกว่าและไม่ติดข้อจำกัด CSS ของ html2canvas
(ข) คอนเทนเนอร์ที่รันรอบอัตโนมัติบล็อก cdnjs โหลด html2canvas ไม่ได้ (Google Fonts ผ่านปกติ)

### รูปแบบ job.json

```json
{
  "ratio": "4:5",
  "slides": [
    { "template": "h1", "name": "ปก",
      "blocks": { "0": { "text": "นโยบายรัฐ · SOLAR" },
                  "2": { "text": "พาดหัว<br>สองบรรทัด" } } }
  ]
}
```

`blocks` คีย์คือ **ลำดับบล็อกในเทมเพลต** (เริ่มที่ 0) ค่าที่ใส่จะทับลงบนบล็อกเดิม
ดูลำดับบล็อกของแต่ละเทมเพลตได้จาก `builder/templates.json`
`ratio` ใส่ต่อสไลด์ได้ด้วย ค่าที่ใช้ได้: `4:5` `1:1` `9:16` `3:4`

ชื่อไฟล์ที่ได้: `01 <name>.png`, `02 <name>.png` … ตามลำดับใน `slides`

### ตัวเช็คล้น

ทุกใบรายงาน `overflow` มาด้วย (เทียบ `scrollHeight` กับ `clientHeight` เหมือน `checkFit`
ในเครื่องมือ) ถ้า `true` แปลว่าข้อความล้นกรอบ ต้องตัดให้สั้นลงแล้วเรนเดอร์ใหม่
รอไว้จนกว่า `document.fonts.ready` ก่อนวัดเสมอ เพราะฟอนต์ไทยโหลดช้ากว่า

### โลโก้

builder ให้ผู้ใช้อัปโหลดโลโก้ตอนรันไทม์ ซึ่งรอบอัตโนมัติทำไม่ได้
ถ้ามี `automation/assets/logo.png` จะฝังเป็น data URI ให้ทุกใบ
ถ้าไม่มี จะใช้ wordmark ข้อความ `24sEnergy` แทน — ไม่ปล่อยกล่อง `LOGO` ออกไปลงเพจ
และรายงาน `logoNote` กลับมาเตือน
