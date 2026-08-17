import Link from "next/link";

const pages = [
  { href: "/archive/home", label: "住小帮首页" },
  { href: "/site/about", label: "关于住小帮" },
  { href: "/site/decorateTips", label: "装修锦囊" },
  { href: "/site/institute", label: "居住研究院" },
  { href: "/home?app_entrance=login", label: "商家入驻平台" },
  { href: "/archive/zhuhaojia", label: "住好家服务页" },
  { href: "/archive/privacy", label: "隐私政策" },
  { href: "/archive/terms", label: "用户协议" },
];

export default function ArchiveIndex() {
  return (
    <main className="archive-index">
      <span className="eyebrow">本地研究存档</span>
      <h1>住小帮像素级存档</h1>
      <p>以下页面保留原站渲染后的 DOM、CSS、JS 与图片资源，仅供本地研究修改。</p>
      <div className="archive-link-grid">
        {pages.map((page) => (
          <Link href={page.href} key={page.href}>
            <b>{page.label}</b>
            <span>打开离线页面</span>
          </Link>
        ))}
      </div>
    </main>
  );
}
