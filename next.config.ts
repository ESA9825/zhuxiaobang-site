import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/home",
        destination: "/archive/merchant/index.html",
      },
      {
        source: "/site/about",
        destination: "/archive/about/index.html",
      },
      {
        source: "/site/about/assets/:path*",
        destination: "/archive/about/assets/:path*",
      },
      {
        source: "/site/decorateTips",
        destination: "/archive/decorate-tips/index.html",
      },
      {
        source: "/site/decorateTips/assets/:path*",
        destination: "/archive/decorate-tips/assets/:path*",
      },
      {
        source: "/site/institute",
        destination: "/archive/institute/index.html",
      },
      {
        source: "/site/institute/assets/:path*",
        destination: "/archive/institute/assets/:path*",
      },
      {
        source: "/passport/aff/web/subject/login_list",
        destination: "/mock/passport-login-list.json",
      },
      {
        source: "/passport/aff/web/subject/login_list/:path*",
        destination: "/mock/passport-login-list.json",
      },
      {
        source: "/homed/business/bservice/account/getinfo",
        destination: "/mock/merchant-account.json",
      },
      {
        source: "/homed/business/bservice/authority/queryRouteList",
        destination: "/mock/merchant-route-list.json",
      },
      {
        source: "/homed/business/bservice/userType/get",
        destination: "/mock/merchant-route-list.json",
      },
      {
        source: "/homed/business/bservice/user/get_user_info",
        destination: "/mock/merchant-user-info.json",
      },
      {
        source: "/homed/business/bservice/opportunity/phoneInit",
        destination: "/mock/merchant-phone-init.json",
      },
      {
        source: "/homed/business/bservice/opportunity/phoneInit/",
        destination: "/mock/merchant-phone-init.json",
      },
      {
        source: "/homed/business/bservice/config/navibarButtons",
        destination: "/mock/merchant-navibar-buttons.json",
      },
      {
        source: "/homed/business/bservice/config/navibarButtons/",
        destination: "/mock/merchant-navibar-buttons.json",
      },
      {
        source: "/homed/business/bservice/businessOrganization/queryPlatformPackInfo",
        destination: "/mock/merchant-pack-info.json",
      },
      {
        source: "/homed/business/bservice/businessOrganization/queryPlatformAllInfo",
        destination: "/mock/merchant-pack-info.json",
      },
      {
        source: "/homed/business/bservice/businessOrganization/queryBySubjectIds",
        destination: "/mock/merchant-empty.json",
      },
      {
        source: "/homed/api/fe/invoke/getNgccSign",
        destination: "/mock/merchant-empty.json",
      },
    ];
  },
};

export default nextConfig;
