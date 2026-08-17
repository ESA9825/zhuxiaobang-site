"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Search, X } from "lucide-react";
import { useState } from "react";
import { navItems } from "@/lib/site-data";

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/" className="brand" aria-label="住家帮首页">
          <span className="brand-mark">住</span>
          <span className="brand-copy">
            <b>住家帮</b>
            <small>轻松住进美好家</small>
          </span>
        </Link>

        <nav className={open ? "site-nav is-open" : "site-nav"}>
          {navItems.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={active ? "is-active" : ""}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="site-header-actions">
          <button className="header-search" aria-label="搜索">
            <Search size={16} />
          </button>
          <Link href="/home?app_entrance=login" className="header-merchant">
            商家入驻
          </Link>
          <Link href="/zhuhaojia" className="header-download">
            下载APP
          </Link>
          <button
            className="header-menu"
            aria-label="打开导航"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X size={19} /> : <Menu size={19} />}
          </button>
        </div>
      </div>
    </header>
  );
}
