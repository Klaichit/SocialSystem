#!/usr/bin/env node
/* Headless renderer สำหรับรอบเช้า
 * ใช้ CSS + renderTemplate() ของ builder/index.html ตรง ๆ ไม่ทำสำเนา layout
 * usage: node render.mjs <job.json> <outdir>
 */
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync, existsSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));

/* playwright ติดตั้งไว้แบบ global ในคอนเทนเนอร์ ESM import ไม่มอง NODE_PATH
   เลย resolve ผ่าน require แล้วไล่หาที่ที่เป็นไปได้ */
const require = createRequire(import.meta.url);
function loadPlaywright() {
  const tries = ['playwright', '/opt/node22/lib/node_modules/playwright'];
  for (const p of tries) { try { return require(p); } catch {} }
  throw new Error('หา playwright ไม่เจอ — ลอง npm i -g playwright');
}
const { chromium } = loadPlaywright();
const BUILDER = resolve(HERE, '..', 'builder', 'index.html');
const LOGO = resolve(HERE, 'assets', 'logo.png');

const [, , jobPath, outDirArg] = process.argv;
if (!jobPath) { console.error('usage: node render.mjs <job.json> <outdir>'); process.exit(1); }

const job = JSON.parse(readFileSync(jobPath, 'utf8'));
const outDir = resolve(outDirArg || job.outDir || '.');
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {}) });
try {
const page = await browser.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));

await page.goto(pathToFileURL(BUILDER).href, { waitUntil: 'load' });
// ฟอนต์ไทยโหลดช้ากว่า element — รอให้ครบก่อนวัดความสูง
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1200);

/* โลโก้: builder ให้ผู้ใช้อัปโหลดตอนรันไทม์ รอบอัตโนมัติไม่มีใครกด
   ถ้ามี automation/assets/logo.png ก็ฝังเป็น data URI ไม่งั้นใช้ wordmark ข้อความแทน
   (ปล่อยกล่อง "LOGO" ออกไปลงเพจไม่ได้) */
let logoNote = null;
if (existsSync(LOGO)) {
  const dataUri = 'data:image/png;base64,' + readFileSync(LOGO).toString('base64');
  await page.evaluate(src => { window.logoSrc = src; }, dataUri);
} else {
  logoNote = 'ไม่มี automation/assets/logo.png — ใช้ wordmark ข้อความแทน';
}
await page.evaluate(() => {
  window.__logo = window.logoSrc
    ? `<img src="${window.logoSrc}">`
    : '<span class="ph" style="border:0;padding:0;letter-spacing:.02em">24sEnergy</span>';
});

const written = [];
for (const [i, slide] of job.slides.entries()) {
  const n = String(i + 1).padStart(2, '0');
  const res = await page.evaluate(({ slide, ratio }) => {
    if (ratio === '16:9') RATIOS['16:9'] = [1920, 1080];
    if (ratio && !RATIOS[ratio]) return { error: 'Unsupported ratio: ' + ratio };
    applyRatio(ratio || '4:5');
    const base = slide.templateData || BY_ID[slide.template];
    if (!base) return { error: 'ไม่รู้จักเทมเพลต ' + slide.template };
    // deep clone แล้วทับค่าตาม blocks ที่ job ส่งมา (index ตรงกับลำดับบล็อกในเทมเพลต)
    const t = JSON.parse(JSON.stringify(base));
    for (const [idx, patch] of Object.entries(slide.blocks || {})) {
      const b = t.blocks[Number(idx)];
      if (!b) return { error: `บล็อก #${idx} ไม่มีในเทมเพลต ${slide.template}` };
      Object.assign(b, patch);
    }
    if (slide.classes) t.classes = slide.classes;

    let host = document.getElementById('shotHost');
    if (!host) {
      host = document.createElement('div');
      host.id = 'shotHost';
      host.style.cssText = 'position:absolute;left:0;top:0;z-index:9999;background:#fff';
      document.body.appendChild(host);
    }
    host.innerHTML = renderTemplate(t);
    host.querySelectorAll('.logo').forEach(l => l.innerHTML = window.__logo);
    const el = host.querySelector('.slide');
    // ตัวเช็คล้นเดียวกับในเครื่องมือ: เนื้อหาสูงเกินกรอบ
    const overflow = el.scrollHeight > el.clientHeight + 2;
    return { overflow, h: el.scrollHeight, ch: el.clientHeight };
  }, { slide, ratio: slide.ratio || job.ratio });

  if (res.error) { console.error('ERROR', res.error); await browser.close(); process.exit(2); }

  await page.evaluate(() => document.fonts.ready);
  const fit = await page.evaluate(() => {
    const el = document.querySelector('#shotHost .slide');
    const bounds = el.getBoundingClientRect();
    const outside = [...el.querySelectorAll('*')].some(child => {
      const rect = child.getBoundingClientRect();
      return rect.width && rect.height && (rect.right > bounds.right + 2 || rect.left < bounds.left - 2 ||
        rect.bottom > bounds.bottom + 2 || rect.top < bounds.top - 2);
    });
    const fontsFailed = [...document.fonts].some(font => font.status === 'error');
    return { overflow: outside || el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2,
      h: el.scrollHeight, ch: el.clientHeight, fontsFailed };
  });
  Object.assign(res, fit);
  if (fit.fontsFailed) throw new Error('Font download failed; retry when Google Fonts is reachable');
  const el = await page.$('#shotHost .slide');
  const name = `${n} ${(slide.name || 'slide').replace(/[\\/:*?"<>|]/g, '-')}.png`;
  const file = join(outDir, name);
  await el.screenshot({ path: file });
  written.push({ file: name, overflow: res.overflow, contentHeight: res.h, frameHeight: res.ch });
  if (res.overflow) console.error(`WARN ${name}: ข้อความล้นกรอบ (${res.h} > ${res.ch}) — ตัดข้อความให้สั้นลง`);
}

await browser.close();
console.log(JSON.stringify({ outDir, logoNote, slides: written, pageErrors: errors }, null, 2));
} finally {
  await browser.close();
}
