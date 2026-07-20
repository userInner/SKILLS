import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const value = flag => {
  const index = args.indexOf(flag);
  if (index < 0 || index + 1 >= args.length) throw new Error(`missing ${flag}`);
  return args[index + 1];
};

const work = path.resolve(value('--work'));
const html = value('--html');
const timelineName = value('--timeline');
const fps = Number(value('--fps'));
const timeline = JSON.parse(await fs.readFile(path.join(work, timelineName), 'utf8'));
const framesDir = path.join(work, 'frames');
await fs.mkdir(framesDir, { recursive: true });
for (const name of await fs.readdir(framesDir)) {
  if (/^frame_\d+\.jpg$/.test(name)) await fs.unlink(path.join(framesDir, name));
}

const count = Math.ceil(timeline.duration * fps);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.join(work, html)).href);
await page.evaluate(data => window.configure(data), timeline);

for (let index = 0; index < count; index++) {
  await page.evaluate(time => window.setFrame(time), index / fps);
  await page.screenshot({
    path: path.join(framesDir, `frame_${String(index).padStart(5, '0')}.jpg`),
    type: 'jpeg',
    quality: 93,
  });
}

await browser.close();
console.log(JSON.stringify({ fps, frames: count, duration: timeline.duration }));
