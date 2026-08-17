import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const repoName =
  process.env.GITHUB_REPOSITORY?.split("/")[1] || "zhuxiaobang-site";
const basePath = `/${repoName}/`;
const publicDir = path.join(root, "public");
const outDir = path.join(root, "out");

const textExtensions = new Set([
  ".css",
  ".html",
  ".js",
  ".json",
  ".md",
  ".svg",
  ".txt",
  ".xml",
]);

function removeDsStore(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      removeDsStore(fullPath);
    } else if (entry.name === ".DS_Store") {
      fs.rmSync(fullPath);
    }
  }
}

function prefixRootUrls(dir) {
  const rootTokenPattern =
    "archive|home|site|zhuhaojia|mock|passport|homed|images|videos|seo|about|decorateTips|institute|account-logout|apply-and-use|privacy|sensitive-personal-message|terms|third-party-sdk|faas|user|merchant";
  const quotedUrl = new RegExp(
    `(["'])\\/(?!\\/|zhuxiaobang-site\\/)(${rootTokenPattern})([^"']*)`,
    "g",
  );
  const entityUrl = new RegExp(
    `(&quot;|&#39;)\\/(?!\\/|zhuxiaobang-site\\/)(${rootTokenPattern})((?:(?!&(?:quot|#39);).)*?)(?=&(?:quot|#39);)`,
    "gs",
  );

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      prefixRootUrls(fullPath);
      continue;
    }
    if (!textExtensions.has(path.extname(entry.name).toLowerCase())) {
      continue;
    }

    let content = fs.readFileSync(fullPath, "utf8");
    let updated = content.replace(quotedUrl, (_match, quote, root, rest) => {
      return `${quote}${basePath}${root}${rest}`;
    });
    updated = updated.replace(entityUrl, (_match, quote, root, rest) => {
      return `${quote}${basePath}${root}${rest}`;
    });
    if (updated !== content) {
      fs.writeFileSync(fullPath, updated);
    }
  }
}

function writeRedirect(relativePath, target) {
  const fullPath = path.join(outDir, relativePath);
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  const destination = `${basePath}${target}`;
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>正在跳转</title>
  <script>
    location.replace(${JSON.stringify(destination)} + location.search + location.hash);
  </script>
</head>
<body></body>
</html>
`;
  fs.writeFileSync(fullPath, html);
}

function copyRewrite(routePath, mockFile) {
  const fullPath = path.join(outDir, ...routePath.split("/"));
  fs.mkdirSync(path.dirname(fullPath), { recursive: true });
  fs.copyFileSync(path.join(publicDir, "mock", mockFile), fullPath);
}

fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });
fs.cpSync(publicDir, outDir, { recursive: true });
removeDsStore(outDir);
fs.writeFileSync(path.join(outDir, ".nojekyll"), "");
prefixRootUrls(outDir);

writeRedirect("index.html", "archive/home/index.html");
writeRedirect("home.html", "archive/merchant/index.html");
writeRedirect("home/index.html", "archive/merchant/index.html");
writeRedirect("about.html", "archive/about/index.html");
writeRedirect("about/index.html", "archive/about/index.html");
writeRedirect("decorateTips.html", "archive/decorate-tips/index.html");
writeRedirect("decorateTips/index.html", "archive/decorate-tips/index.html");
writeRedirect("institute.html", "archive/institute/index.html");
writeRedirect("institute/index.html", "archive/institute/index.html");
writeRedirect("zhuhaojia.html", "archive/zhuhaojia/index.html");
writeRedirect("zhuhaojia/index.html", "archive/zhuhaojia/index.html");
writeRedirect("site/home.html", "archive/home/index.html");
writeRedirect("site/home/index.html", "archive/home/index.html");
writeRedirect("site/about.html", "archive/about/index.html");
writeRedirect("site/about/index.html", "archive/about/index.html");
writeRedirect("site/decorateTips.html", "archive/decorate-tips/index.html");
writeRedirect(
  "site/decorateTips/index.html",
  "archive/decorate-tips/index.html",
);
writeRedirect("site/institute.html", "archive/institute/index.html");
writeRedirect("site/institute/index.html", "archive/institute/index.html");
writeRedirect("404.html", "archive/home/index.html");

const rewrites = [
  ["passport/aff/web/subject/login_list", "passport-login-list.json"],
  ["homed/business/bservice/account/getinfo", "merchant-account.json"],
  ["homed/business/bservice/authority/queryRouteList", "merchant-route-list.json"],
  ["homed/business/bservice/userType/get", "merchant-route-list.json"],
  ["homed/business/bservice/user/get_user_info", "merchant-user-info.json"],
  ["homed/business/bservice/opportunity/phoneInit", "merchant-phone-init.json"],
  [
    "homed/business/bservice/businessOrganization/queryPlatformPackInfo",
    "merchant-pack-info.json",
  ],
  [
    "homed/business/bservice/businessOrganization/queryPlatformAllInfo",
    "merchant-pack-info.json",
  ],
  [
    "homed/business/bservice/businessOrganization/queryBySubjectIds",
    "merchant-empty.json",
  ],
  ["homed/api/fe/invoke/getNgccSign", "merchant-empty.json"],
];

for (const [routePath, mockFile] of rewrites) {
  copyRewrite(routePath, mockFile);
}

console.log(`Built ${outDir} with base path ${basePath}`);
