# 24sEnergy Content Vault

Vault สำหรับคิดและร่างคอนเทนต์ carousel ก่อนเอาไปทำภาพจริงใน Carousel Builder

## วิธีติดตั้ง
1. เปิด Obsidian → Open folder as vault → เลือกโฟลเดอร์นี้
2. Settings → Community plugins → เปิด **Dataview** (จำเป็นสำหรับ Dashboard)
3. Settings → Templates → Template folder location = `_templates`

ไม่ต้องลง plugin อื่น ถ้าอยากได้ auto-fill วันที่ค่อยลง Templater ทีหลัง

## โฟลเดอร์
| โฟลเดอร์ | ใส่อะไร |
|---|---|
| `posts/` | หนึ่งไฟล์ = หนึ่งโพสต์ ตั้งแต่ไอเดียจนลงจริง |
| `references/` | โพสต์จากเพจอื่นที่ชอบ + โครงที่ถอดได้ |
| `products/` | สินค้าแต่ละตัว สเปก จุดขาย |
| `notes/` | ความรู้ทั่วไป ตัวเลข ข้อมูลอ้างอิง |
| `_templates/` | แม่แบบโน้ต |

## เวิร์กโฟลว์
ไอเดีย → `posts/` (status: idea) → เขียนข้อความครบ (draft) → เลือกเทมเพลต เช่น `p2` (ready)
→ เปิด Carousel Builder ทำภาพ → ลงจริง (posted + ใส่ post_date)

`Dashboard.md` คือหน้าที่เปิดทุกวัน ดูว่าอะไรค้างอยู่ตรงไหน
