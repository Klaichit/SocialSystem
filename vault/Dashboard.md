# Dashboard

## ค้างอยู่ — ต้องเขียนต่อ
```dataview
TABLE pillar AS "เสา", status AS "สถานะ", template AS "เทมเพลต"
FROM "posts"
WHERE status != "posted"
SORT status ASC, file.name ASC
```

## พร้อมทำภาพแล้ว
```dataview
TABLE template AS "เทมเพลต", ratio AS "สัดส่วน", platform AS "ลงที่ไหน"
FROM "posts"
WHERE status = "ready"
```

## ลงไปแล้ว 10 ชิ้นล่าสุด
```dataview
TABLE post_date AS "วันลง", pillar AS "เสา"
FROM "posts"
WHERE status = "posted"
SORT post_date DESC
LIMIT 10
```

## นับตามเสา — เช็คว่าลงเอียงไปทางไหนไหม
```dataview
TABLE length(rows) AS "จำนวน"
FROM "posts"
WHERE status = "posted"
GROUP BY pillar
```

## รีเฟอเรนซ์ที่ยังไม่ได้แปลงเป็นเทมเพลต
```dataview
TABLE source_page AS "เพจ", layout_kind AS "โครง"
FROM "references"
WHERE converted = false
```

## สินค้าทั้งหมด
```dataview
TABLE category AS "หมวด", brand AS "แบรนด์"
FROM "products"
```
