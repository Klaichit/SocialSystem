# Notion → ภาพโพสต์ Social Media → Google Drive

**1 หัวข้อ = 1 ภาพ** สำหรับอุตสาหกรรมโซลาร์เซลล์ ใช้แบรนด์ 24sEnergy
ออนไลน์ผ่าน GitHub Actions ทุก 3 ชั่วโมง หรือกด Run workflow เอง

## เปิดใช้งานออนไลน์

1. นำโค้ดนี้เข้า default branch ของ SocialSystem
2. ทำขั้นตอนเชื่อมต่อบัญชีด้านล่างบนเครื่องของคุณครั้งเดียว
3. หลังโหลด Google OAuth environment แล้ว รัน `python -X utf8 worker.py --init-cloud-state`
   เพื่อสร้างไฟล์ประวัติงานส่วนตัวใน Drive เก็บค่า DRIVE_STATE_FILE_ID ที่สคริปต์แสดง
   สร้างเพียงครั้งเดียวและใช้ ID เดิมตลอด ห้ามสร้าง state ใหม่ทุกครั้งที่รัน
4. ไป GitHub repository → Settings → Secrets and variables → Actions → Secrets
   เพิ่ม `NOTION_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`,
   และ `DRIVE_STATE_FILE_ID` (ไม่ใส่ค่าในโค้ดหรือข้อความแชต)
5. ในแท็บ Variables เพิ่ม `SOCIAL_IMAGES_ENABLED` = `true`
6. ไป Actions → **Notion to social image** → **Run workflow** เพื่อทดสอบครั้งแรก

รอบอัตโนมัติเวลาไทย 01:17, 04:17, 07:17, 10:17, 13:17, 16:17, 19:17, 22:17
GitHub อาจเริ่มช้ากว่าเวลาเหล่านี้ได้ ตั้งนาที 17 เพื่อลดการชนกับรอบต้นชั่วโมง
กดเองได้ตลอด; workflow concurrency ป้องกันรอบซ้อน และอ่านประวัติเดิมจาก Drive
ไม่ต้องเปิดคอมไว้ ไม่ต้องตั้ง Windows service และไม่อัปโหลดภาพเป็น GitHub artifact
หาก repository เป็น public และไม่มี activity 60 วัน GitHub อาจปิด scheduled workflow
ให้ตรวจหน้า Actions และเปิดอีกครั้ง ค่าใช้บริการขึ้นกับสิทธิ์/โควตา GitHub Actions ของบัญชี
หยุดระบบได้โดยเปลี่ยน `SOCIAL_IMAGES_ENABLED` เป็น `false`

ห้ามเปิด local worker พร้อม workflow ออนไลน์: ใช้ worker เพียง deployment เดียว
ไฟล์ state อยู่ใน Drive และสืบทอดสิทธิ์จากโฟลเดอร์ปลายทาง ไม่ควรลบหรือแก้เองระหว่างรัน

เอกสาร scheduling: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

## ทางเลือก: รันในเครื่อง

ตัว worker ใหม่ตรวจ Notion ทุก 60 วินาที และรับแถวที่ `ขั้นตอน = อนุมัติแล้ว`,
ติ๊ก `DK อนุมัติ` และยังไม่ติ๊ก `เผยแพร่แล้ว` การตรวจเป็น polling ไม่ใช่ webhook:
เมื่อโปรแกรมเปิดอยู่จะพบสถานะใหม่ภายในประมาณ 60 วินาที บวกเวลาคิวและเรนเดอร์
การเปิดครั้งแรกจะรับงานที่เข้าเงื่อนไขอยู่แล้วด้วย

ใช้ database และ Drive folder ที่ตั้งไว้ใน `worker.config.json` ไม่เขียนสถานะกลับ Notion
และไม่เปลี่ยนสิทธิ์แชร์ Drive ระบบนี้แยกจาก routine รอบเช้าใน MORNING.md:
ควรหยุด routine เดิมก่อนเปิด worker เพื่อไม่ให้สองระบบทำโพสต์เดียวกัน

## วิธีออกแบบภาพ

- ใช้ h1 เป็นแนวทางพาดหัว, m5 สำหรับข่าว, h8 สำหรับข้อความเป็นข้อ
- ใช้ classes, CSS, สีม่วง #6A2DAF, ฟอนต์ และ renderer ของ builder เดิม
- ปรับบล็อกให้เป็นภาพเดียว มีพาดหัวและภาพเส้นแผงโซลาร์แบบ industrial
- ใส่สรุปบนภาพเฉพาะเมื่อสั้นไม่เกิน 140 ตัว ถ้ายาวกว่านั้นเก็บรายละเอียดเต็มใน caption.txt
- คงข้อควรทราบจาก Factual Guardrails และแหล่งข่าว ข้อความ Notion ถูก escape ก่อนเข้า HTML
- สร้างภาพเดียวตามสัดส่วนที่เลือก ถ้าเลือกหลายค่าใช้ 4:5 ก่อน หรือค่าแรกถ้าไม่มี 4:5
- เป็นการออกแบบตามกฎและเรนเดอร์ HTML ไม่ได้เรียกโมเดล AI วาดภาพหรือเกลาข้อความ
- ข้อความพาดหัวเกิน 120 ตัว/ข้อควรทราบเกิน 120 ตัวจะรายงานให้แก้ใน Notion ไม่ตัดข้อเท็จจริงทิ้ง
- ตรวจกรอบล้นหลังโหลดฟอนต์ ถ้าล้นหรือโหลดฟอนต์ไม่สำเร็จจะไม่อัปโหลด
- วางโลโก้จริงที่ `automation/assets/logo.png` ได้ หากไม่มีใช้ wordmark 24sEnergy

## ติดตั้ง

ต้องมี Python 3.10+, Node.js 22+, อินเทอร์เน็ตสำหรับ Notion, Google Drive และ Google Fonts

```powershell
cd automation
npm ci
npx playwright install chromium
python -X utf8 -m unittest discover -s tests
```

ไม่เพิ่ม build step ให้ builder เดิม dependency นี้ใช้เฉพาะระบบอัตโนมัติ
ใช้ Chrome ที่ติดตั้งอยู่แทนได้โดยตั้ง `CHROME_PATH` เป็น path ของ chrome.exe

## เชื่อมต่อบัญชี (ครั้งเดียว)

การเชื่อม Notion/Drive ใน Codex ไม่ได้มอบ token ให้โปรแกรมภายนอกอัตโนมัติ
ต้องตั้งค่าด้านล่างในสภาพแวดล้อมของเครื่องที่จะเปิด worker ห้าม commit secrets

1. สร้าง Notion internal integration ที่ https://www.notion.so/profile/integrations
   ให้สิทธิ์อ่านเนื้อหา และเพิ่ม connection ให้ฐานข้อมูล Content Hub ที่ผู้ใช้ระบุ
   ตั้ง `NOTION_TOKEN` เป็น integration token
2. ใน Google Cloud เปิด Google Drive API แล้วสร้าง OAuth client แบบ Desktop app
   ใช้ `python google_auth.py path/to/client_secret.json` เปิดลิงก์ที่แสดงและอนุญาตบัญชี
   ที่เข้าถึงโฟลเดอร์ Facebook ได้ สคริปต์เก็บค่าลง `.runtime/google-oauth.json`
   OAuth scope `drive` จำเป็นเพื่อเข้าถึงโฟลเดอร์เดิมที่แอปไม่ได้สร้าง ใช้บัญชีที่ต้องการเท่านั้น
   หาก OAuth app อยู่ใน External Testing อาจต้องอนุญาตใหม่เมื่อ refresh token หมดอายุ
3. โหลด `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` จากไฟล์นี้
   ผ่าน PowerShell ตามด้านล่าง (ไม่มีการพิมพ์ค่า secret ลงหน้าจอ)

```powershell
$googleAuth = Get-Content .runtime/google-oauth.json -Raw | ConvertFrom-Json
$env:GOOGLE_CLIENT_ID = $googleAuth.client_id
$env:GOOGLE_CLIENT_SECRET = $googleAuth.client_secret
$env:GOOGLE_REFRESH_TOKEN = $googleAuth.refresh_token
# ตั้ง NOTION_TOKEN ใน environment อย่างปลอดภัยก่อนรัน
python -X utf8 worker.py --once
python -X utf8 worker.py
```

เครื่องต้องเปิดและ worker ต้องทำงานต่อเนื่อง ปิดด้วย Ctrl+C; โปรแกรมนี้ไม่ได้ติดตั้ง
Windows service หรือ scheduled task ให้เอง ถ้ารันบน server ให้ใช้ process manager
พร้อม persistent disk สำหรับ `.runtime` ห้ามรันหลายเครื่องด้วย state คนละชุด

## การกู้คืน / ตรวจงาน

งานเสร็จแล้วจะพิมพ์ page ID และ Drive folder ID ใน log ส่วนรูปและแคปชันอยู่ใน
โฟลเดอร์ปลายทางจริง ไม่มีการส่ง PNG ผ่านบทสนทนาหรือ commit รูปลง GitHub

`.runtime/jobs.json` เก็บ snapshot ของข้อมูลและ ID ที่จองไว้ก่อนเขียน Drive:
หากอัปโหลดสำเร็จแต่ response หาย รันใหม่จะตรวจ ID เดิมและข้ามไฟล์นั้น
ข้อผิดพลาดของงานหนึ่งไม่ขวางงานอื่น worker จะลองอีกครั้งในรอบถัดไป
ไฟล์ที่อัปโหลดสำเร็จก่อน error จะยังคงอยู่; งานจะ mark done เมื่อครบทุกไฟล์

แต่ละหน้าเรนเดอร์ครั้งเดียว แม้เปลี่ยนสถานะออกแล้วกลับมาอีกก็ไม่สร้างซ้ำ
ต้องการเวอร์ชันใหม่ให้ duplicate หน้าใน Notion เพื่อได้ page ID ใหม่
งานที่เริ่มแล้วใช้ snapshot เดิมเพื่อให้รูปกับแคปชันเป็นเวอร์ชันเดียวกัน
กรณีงานค้างเพราะข้อความยาว ให้หยุด worker ลบ entry ของ page ID นั้นจาก jobs.json
แล้วแก้ข้อความใน Notionและเริ่มใหม่ (เก็บสำเนา jobs.json ไว้ก่อน)
หากงานเคยอัปโหลดบางไฟล์แล้ว ควร duplicate หน้าแทนการลบ entry

ข้อจำกัด: ช่วงสถานะที่เปลี่ยนกลับก่อน polling อาจตรวจไม่พบ และยังไม่มีการตรวจ
ความถูกต้องทางบรรณาธิการ/การซ้อนทับภายในกรอบทุกรูปแบบ ควรตรวจภาพก่อนเผยแพร่จริง

เอกสาร API: https://developers.notion.com/reference/query-a-data-source
และ https://developers.google.com/workspace/drive/api/guides/manage-uploads
