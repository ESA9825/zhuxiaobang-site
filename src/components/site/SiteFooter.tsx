import Link from "next/link";

const footerColumns = [
  {
    title: "产品",
    links: [
      { label: "装修案例", href: "/cases" },
      { label: "装修锦囊", href: "/decorate-tips" },
      { label: "居住研究院", href: "/institute" },
      { label: "装修工具", href: "/#tools" },
    ],
  },
  {
    title: "合作",
    links: [
      { label: "业务合作", href: "/business" },
      { label: "商家入驻", href: "/home?app_entrance=login" },
      { label: "设计师合作", href: "/business" },
      { label: "品牌伙伴", href: "/business" },
    ],
  },
  {
    title: "关于",
    links: [
      { label: "关于我们", href: "/about" },
      { label: "隐私协议", href: "/privacy" },
      { label: "用户协议", href: "/terms" },
      { label: "住好家服务", href: "/zhuhaojia" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-main">
        <div className="footer-brand">
          <span className="footer-brand-mark">住</span>
          <div>
            <b>住家帮</b>
            <p>装修灵感、家装知识和服务优选的一站式参考平台。</p>
          </div>
        </div>
        <div className="footer-columns">
          {footerColumns.map((column) => (
            <div className="footer-column" key={column.title}>
              <h3>{column.title}</h3>
              {column.links.map((link) => (
                <Link key={link.label} href={link.href}>
                  {link.label}
                </Link>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="site-footer-bottom">
        <p>本页面为学习参考版，非住小帮官方网站。</p>
        <p>© 2026 住家帮参考项目</p>
      </div>
    </footer>
  );
}
