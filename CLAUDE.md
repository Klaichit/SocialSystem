# CLAUDE.md — SocialSystem

บริบทสำหรับทำงานต่อกับโปรเจกต์นี้ อ่านไฟล์นี้ก่อนแก้อะไร

## โปรเจกต์นี้คืออะไร

ระบบผลิตคอนเทนต์ carousel ให้ **24sEnergy** บริษัทไทยด้าน BESS + Solar PV + EV charging
ผู้ใช้คนเดียว (DK, game artist / technical artist) ทำเองทั้งหมด ไม่มีทีมมาแก้ต่อ
เลยเลือกทาง HTML ที่คุม layout ได้แม่น แทน Canva ที่แชร์ให้คนอื่นแก้ง่ายกว่า

ปลายทางคือโพสต์ลง Facebook Page / Instagram / TikTok กลุ่มเป้าหมายผสมทั้ง
โรงงาน B2B, เจ้าของกิจการ, และผู้รับเหมา

## สแตก

ไม่มี build step ไม่มี dependency manager
`builder/index.html` เป็นไฟล์เดียวจบ เปิดด้วยเบราว์เซอร์ตรง ๆ (`file://`)

- vanilla JS ทั้งหมด ไม่มี framework
- html2canvas 1.4.1 จาก cdnjs — ใช้ตอน export PNG
- Google Fonts — โหลด 3 ตัวตอนเปิด ที่เหลือ lazy-load ตอนเลือก

**ข้อจำกัดที่กำหนดสถาปัตยกรรม:** `file://` บล็อก `fetch` ไฟล์ในเครื่อง
`templates.json` จึงถูกฝังใน `<script type="application/json" id="tplData">` ใน `index.html`
และมี file picker ให้โหลดไฟล์ทับตอนรันไทม์ ถ้าแก้ `templates.json` แล้วอยากให้เป็น
ค่าเริ่มต้นถาวร **ต้องแทนที่บล็อกในตัว `index.html` ด้วย** ไม่งั้นจะไม่มีผลตอนเปิดครั้งถัดไป

## แผนผังไฟล์

```
builder/index.html      ทั้งระบบอยู่ในนี้: CSS + renderer + UI
builder/templates.json  ชุดเทมเพลตต้นฉบับ (สำเนาของที่ฝังใน index.html)
vault/                  Obsidian vault สำหรับร่างเนื้อหา ไม่เกี่ยวกับโค้ด
```

โครงภายใน `index.html` ตามลำดับ:
1. `<style>` — design tokens, สไตล์แอป, สไตล์สไลด์, แคตตาล็อก, toolbar
2. `<aside class="rail">` — แผงควบคุมซ้าย
3. `<main id="work">` — รายการสไลด์ที่กำลังทำ
4. `#gal` — แคตตาล็อกเทมเพลตเต็มจอ
5. `#tbar` — แถบปรับสไตล์รายข้อความ
6. `#tplData` — JSON เทมเพลต
7. `<script>` — renderer + logic ทั้งหมด

## สถาปัตยกรรมหลัก: เทมเพลตคือข้อมูล

ไม่มี layout ฝังในโค้ด เทมเพลตหนึ่งตัวหน้าตาแบบนี้:

```json
{
  "id": "p2",
  "group": "prod",
  "name": "สินค้า + สเปก 3 ช่อง",
  "classes": [],
  "blocks": [ { "type": "meta", "pill": "BESS", "date": "Hithium" }, ... ]
}
```

`renderTemplate(t)` คืน HTML string ของ `.slide` โดยเรียก `blocks(list)` ซึ่งวนเรียก
`R[type](block)` แต่ละบล็อกใน object `R` เป็น pure function: block object → HTML string
ไม่แตะ DOM ไม่มี side effect เพิ่มบล็อกชนิดใหม่ = เพิ่ม key ใน `R` + CSS ที่เกี่ยวข้อง

`classes` ของสไลด์ที่ใช้ได้: `dark` (พื้นม่วง), `ink` (พื้นดำ), `soft` (พื้นม่วงอ่อน),
`has-photo` (ภาพเต็มพร้อม gradient ม่วงทับ), `flush` (ตัด padding เป็น 0)

### บล็อกทั้ง 34 ชนิด

ฟิลด์ในวงเล็บคือที่ใช้จริงอยู่ตอนนี้ ทุกบล็อกรับ `style` เป็น inline CSS ได้

| type | ฟิลด์ | หมายเหตุ |
|---|---|---|
| `eyebrow` | text | หัวเรื่องเล็ก mono สีแบรนด์ |
| `head` | text, size, style | size: `xl` `sm` `xs` หรือเว้นว่าง |
| `body` | text, size, style | size: `sm` |
| `pill` | text | badge มุมโค้ง |
| `date` | text | mono สีเทา |
| `rule` | — | แถบขีดสั้น |
| `spacer` | flex | ตัวดันระยะ ค่าปกติ `flex:1` |
| `gap` | h | ช่องว่างความสูงคงที่ (px) |
| `meta` | pill, date | แถวบนสุด badge ซ้าย + วันที่ขวา |
| `mockup` | mod | ช่องวางรูป `mod`: `bare` (ไม่มีพื้น), `grow` (flex:1) |
| `photo` | — | ภาพเต็มสไลด์ ต้องคู่กับ class `has-photo` |
| `stat` | value, unit, caption | ตัวเลขใหญ่ mono |
| `specs` | items[{k,v}] | สเปก 3 ช่องแนวนอน |
| `speclist` | items[{k,v}] | สเปกแนวตั้งมีเส้นคั่น |
| `price` | label, value | บล็อกราคา/CTA |
| `dots` | items[string] | ลิสต์จุดเด่นมีเลขในวงกลม |
| `checklist` | items[string] | เช็คลิสต์มีเลขนำ |
| `tf` | items[{mark,text}] | `mark`: `yes` หรือ `no` |
| `cols` | items[{k,v}] | สองคอลัมน์เทียบกัน |
| `sideby` | columns[[block]] | คอลัมน์ที่ใส่บล็อกซ้อนได้ |
| `halfsplit` | halves[{variant,blocks}] | `variant`: `a` (ขาว) `b` (ม่วง) |
| `lr` | mockup, blocks | รูปซ้าย ข้อความขวา |
| `grid4` | items[string] | ตาราง 4 ช่องวางรูป |
| `wrap` | blocks, class, style | ตัวห่อสำหรับ layout พิเศษ |
| `quote` | text, byline | คำพูดพร้อมเครื่องหมาย |
| `bigword` | lines[string] | คำใหญ่ใช้ฟอนต์ display |
| `band` | text | พาดหัวบนแถบม่วงเต็มความกว้าง |
| `idx` | text | เลขนำใหญ่ |
| `qmark` | style | เครื่องหมายคำถามพื้นหลัง |
| `tagover` | text | ข้อความจาง ๆ ทับมุมขวาบน |
| `halo` | — | วงเรืองแสงพื้นหลัง |
| `source` | text | บรรทัดที่มาข่าว |
| `halfk` | text | ป้ายกำกับใน halfsplit |
| `foot` | right, mt | โลโก้ + ข้อความขวา ทุกสไลด์ควรมี |

## CSS custom properties

ตัวแปรพวกนี้คือกลไกหลัก ห้ามฮาร์ดโค้ดค่าที่ทับซ้อนกับมัน

**แบรนด์ (ห้ามแก้ ล็อกมาจากเว็บ 24sEnergy)**
`--brand:#6A2DAF` `--brand-dark:#4d1f80` `--brand-light:#8b4dd6` `--brand-soft:#f1e9fb`
`--brand-2:#3F3F3F` `--ink:#1a1a1a` `--ink-2:#4a4a4a` `--muted:#8a8a8a` `--line:#e8e8ec`
`--bg-dark:#1a1a1f` `--radius:14px` `--radius-sm:10px`

**ขนาดผลลัพธ์** — `--sw` `--sh` (ขนาดสไลด์จริง), `--stage-h` (พรีวิว กว้าง 360 คงที่),
`--gal-h` (รูปย่อในแคตตาล็อก กว้าง 200 คงที่) ตั้งค่าโดย `applyRatio()`

**ตัวอักษร** — `--font-head` `--font-body` `--font-display` `--mono` `--tscale`
`--tscale` คูณเข้าไปใน `font-size:calc(Npx * var(--tscale))` ทั้ง 39 จุด
**บล็อกใหม่ทุกตัวต้องใช้ calc นี้ด้วย** ไม่งั้นสไลเดอร์ขนาดจะข้ามบล็อกนั้น

**สัญลักษณ์** — `--sym-yes` `--sym-no` `--sym-quote` `--sym-q` `--chk-counter` `--dot-counter`
สัญลักษณ์ทั้งหมดวาดผ่าน `::before { content: var(--sym-*) }` และ CSS counter
ทำแบบนี้เพราะสลับชุดสัญลักษณ์ได้สดโดยไม่ต้อง re-render (ข้อความที่ผู้ใช้พิมพ์จะไม่หาย)
**อย่าเขียนอักขระสัญลักษณ์ตรง ๆ ใน renderer** ให้ปล่อย element ว่างแล้วให้ CSS เติม

## ฟังก์ชันสำคัญ

| ฟังก์ชัน | หน้าที่ |
|---|---|
| `renderTemplate(t)` / `blocks(list)` / `R` | แปลง JSON → HTML |
| `makeSlot(id)` | สร้างการ์ดสไลด์หนึ่งใบพร้อมแถบเครื่องมือ |
| `enableDrop(slide)` | ผูก drag-drop รูปให้ทุก `.photo` และ `.mockup` แยกช่อง |
| `checkFit(slot)` / `checkAll()` / `checkSoon()` | ตรวจข้อความล้นและทับกัน |
| `applyRatio(key)` | เปลี่ยนสัดส่วนทั้งระบบ |
| `applySyms(key)` | สลับชุดสัญลักษณ์ |
| `ensureFont(name)` | lazy-load Google Font |
| `shoot(slot, n)` | export PNG ใบเดียว |
| `indexData()` / `buildPickers()` / `buildGal()` | สร้าง index และ UI จาก DATA |

### ตัวเช็คล้น/ทับ — ตรรกะ

`checkFit` ตรวจสามชั้นตามลำดับ หยุดทันทีที่เจอปัญหา:
1. `slide.scrollHeight > clientHeight + 2` — เนื้อหาล้นกรอบ
2. ทุก element ใน `WATCH` ที่ `getBoundingClientRect()` หลุดขอบสไลด์
3. บล็อกที่ position static และไม่อยู่ใน container แนวนอน (`.cols .sideby .grid4 .lr
   .specs .meta .foot .halfsplit`) ถ้าขอบบนของตัวถัดไปสูงกว่าขอบล่างของตัวก่อนเกิน 1.5px = ทับกัน

รันแบบ debounce 180ms ตอนพิมพ์ และรันซ้ำหลัง `document.fonts.ready`
(ฟอนต์ไทยโหลดช้ากว่า ความสูงจะเปลี่ยนหลังโหลดเสร็จ)

**ถ้าเพิ่มบล็อกใหม่ที่มีข้อความ ต้องเพิ่ม selector เข้าไปใน `WATCH` ด้วย**

### export

`shoot()` ถอด `transform: scale(.3333)` ออกชั่วคราว ขยาย stage เป็นขนาดจริง
ยิง html2canvas แล้วคืนค่าเดิมใน `finally` ถ้าแก้ตรงนี้ระวังอย่าให้ throw ก่อนคืนค่า
ไม่งั้นพรีวิวจะค้างขนาดเต็ม

## กฎที่ต้องรักษา

1. **ไม่แตะสีแบรนด์** ม่วง `#6A2DAF` กับชุดสีที่เหลือล็อกมาจากเว็บบริษัท ต้องตรงกัน
2. **โทน B2B-industrial** ไม่ใช่ lifestyle ตัวเลขและสเปกใช้ mono เสมอ นั่นคือสิ่งที่ทำให้
   ดู technical ไม่ใช่เพจขายของทั่วไป
3. **ไม่เพิ่ม build step** ต้องเปิดไฟล์จากเครื่องแล้วใช้ได้ทันที
4. **ไม่ใช้ localStorage** งานถูกออกแบบให้อยู่ใน memory ระหว่าง session เท่านั้น
5. ทุกสไลด์ต้องมี `foot` เพื่อให้โลโก้ติดทุกใบ

## ข้อจำกัดที่รู้อยู่ (อย่าพยายาม "แก้" โดยไม่คุยก่อน)

- **ไม่ดึงข้อมูลจาก Facebook อัตโนมัติ** CrowdTangle ปิดไปแล้ว Meta Content Library
  เปิดให้เฉพาะนักวิจัยในสถาบัน และ Page Public Content Access แทบไม่อนุมัติเชิงพาณิชย์
  วิธีที่ใช้คือเก็บภาพอ้างอิงเองแล้วถอดเป็นบล็อก JSON
- **Anton ไม่มี glyph ไทย** ใช้ได้เฉพาะข้อความอังกฤษ (บล็อก `bigword`)
- **สไตล์รายข้อความเป็น inline style** ไม่ถูกเซฟกลับเข้า `templates.json`
- **1:1 แคบกว่า 4:5 อยู่ 270px** เทมเพลตเนื้อหาแน่นอย่าง `p10` `h8` มีสิทธิ์ล้น
- html2canvas ไม่รองรับ CSS บางตัว ถ้าเพิ่มเอฟเฟกต์ใหม่ให้ทดสอบ export ทุกครั้ง

## งานที่พอจะทำต่อได้

- เขียนสไตล์ที่ปรับรายข้อความกลับเข้า `templates.json` เป็น override ถาวร
- ปุ่มบันทึก/โหลด "ชุดสไลด์ที่ทำค้างไว้" เป็นไฟล์ JSON
- export ทั้งชุดเป็น zip ใบเดียวแทนดาวน์โหลดทีละใบ
- ไอคอน SVG ประจำหมวด (BESS / Solar / EV) ที่รับสีจาก CSS variable ได้
  (เคยคุยแล้วว่าอย่าใช้ emoji เพราะคุมสีแบรนด์ใน PNG ไม่ได้)
- preset สัดส่วนต่อสไลด์ แทนที่จะเป็นค่าเดียวทั้งชุด
