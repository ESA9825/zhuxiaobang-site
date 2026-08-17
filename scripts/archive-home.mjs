import { promises as fs } from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const sourceHtml =
  process.argv[2] ?? "/Users/esa/dev/zhuxiaobang-archive/dom/home.html";
const outputName = process.argv[3] ?? "home";
const outputRoot =
  process.env.ARCHIVE_OUTPUT_DIR ?? "/Users/esa/dev/zhuxiaobang-clone/public/archive";
const outputDir = path.join(outputRoot, outputName);

function normalizeUrl(raw) {
  const value = raw
    .trim()
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&")
    .replace(/^['"]|['"]$/g, "");
  if (!value || value.startsWith("data:") || value.startsWith("#")) return null;
  if (value.startsWith("//")) return `https:${value}`;
  try {
    return new URL(value, "https://www.zhuxiaobang.com").toString();
  } catch {
    return null;
  }
}

function assetKind(url) {
  const clean = url.split("?")[0].split("#")[0].toLowerCase();
  if (clean.endsWith(".css")) return "css";
  if (clean.endsWith(".js")) return "js";
  if (/\.(png|jpe?g|webp|gif|svg|ico|avif|bmp)$/.test(clean)) return "img";
  return null;
}

async function download(url) {
  const normalized = normalizeUrl(url);
  if (!normalized) return null;
  const kind = assetKind(normalized);
  if (!kind) return null;
  const hash = crypto.createHash("sha1").update(normalized).digest("hex").slice(0, 12);
  const ext = path.extname(new URL(normalized).pathname) || "";
  const file = `${hash}${ext || ".bin"}`;
  const dest = path.join(outputDir, "assets", kind, file);
  try {
    await fs.access(dest);
    return `assets/${kind}/${file}`;
  } catch {
    // continue to download
  }
  const response = await fetch(normalized, {
    headers: {
      "user-agent": "Mozilla/5.0",
      referer: "https://www.zhuxiaobang.com/",
    },
  });
  if (!response.ok) return null;
  const buffer = Buffer.from(await response.arrayBuffer());
  await fs.mkdir(path.dirname(dest), { recursive: true });
  await fs.writeFile(dest, buffer);
  return `assets/${kind}/${file}`;
}

async function rewriteCss(css, cssRelDir) {
  const matches = [...css.matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)];
  const replacements = new Map();
  for (const match of matches) {
    const raw = match[2];
    if (raw.startsWith("data:")) continue;
    const local = await download(raw);
    if (local) {
      const cssAbsolute = path.join(outputDir, cssRelDir, "style.css");
      const relative = path
        .relative(path.dirname(cssAbsolute), path.join(outputDir, local))
        .split(path.sep)
        .join("/");
      replacements.set(raw, relative);
    }
  }
  let next = css;
  for (const [raw, local] of replacements) {
    next = next.split(raw).join(local);
  }
  return next;
}

await fs.mkdir(path.join(outputDir, "assets/css"), { recursive: true });
await fs.mkdir(path.join(outputDir, "assets/js"), { recursive: true });
await fs.mkdir(path.join(outputDir, "assets/img"), { recursive: true });

let html = await fs.readFile(sourceHtml, "utf8");
const attrMatches = [...html.matchAll(/(?:href|src)=["']([^"']+)["']/g)];
const urlMatches = [...html.matchAll(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g)];

for (const match of [...attrMatches, ...urlMatches]) {
  const raw = match[2] ?? match[1];
  const normalized = normalizeUrl(raw);
  if (!normalized) continue;
  const kind = assetKind(normalized);
  if (!kind) continue;
  const local = await download(normalized);
  if (local) html = html.split(raw).join(local);
}

// The SPA pages are served from /site/<page>, so use absolute archive paths
// for assets. This avoids browser relative-path resolution changing the URL.
html = html.replace(
  /(href|src)="assets\//g,
  `$1="/archive/${outputName}/assets/`,
);

const cssLinks = [...html.matchAll(/<link[^>]+href=["']([^"']+\.css)["'][^>]*>/g)];
for (const match of cssLinks) {
  const cssPath = match[1];
  if (!cssPath.startsWith("assets/")) continue;
  const absolute = path.join(outputDir, cssPath);
  try {
    const css = await fs.readFile(absolute, "utf8");
    await fs.writeFile(absolute, await rewriteCss(css, path.dirname(cssPath)));
  } catch {
    // keep the original css if it cannot be rewritten
  }
}

await fs.writeFile(path.join(outputDir, "index.html"), html);
console.log("archive written:", outputDir);
