import { BarChart3, Handshake, Megaphone, PackageSearch, Users } from "lucide-react";
import { PageHero } from "@/components/site/PageHero";

const businessItems = [
  { icon: Users, title: "品牌合作", text: "联合内容、活动和案例，触达正在做装修决策的用户。" },
  { icon: PackageSearch, title: "主材合作", text: "让优质建材与家居产品进入真实场景和选购清单。" },
  { icon: Megaphone, title: "内容共创", text: "与达人、设计师共同生产专业且可传播的家装内容。" },
  { icon: BarChart3, title: "数据洞察", text: "基于平台趋势为行业伙伴提供消费与风格洞察。" },
];

export default function BusinessPage() {
  return (
    <>
      <PageHero
        eyebrow="业务合作"
        title="和靠谱伙伴，一起把家装做好"
        description="为品牌、商家、设计师与内容创作者提供合作入口和经营支持。"
        image="/images/research.jpg"
        compact
      />
      <section className="content-section">
        <div className="section-heading centered">
          <span className="eyebrow">合作方向</span>
          <h2>围绕用户真实需求展开合作</h2>
        </div>
        <div className="business-grid">
          {businessItems.map((item) => (
            <div className="business-card" key={item.title}>
              <item.icon size={20} />
              <h3>{item.title}</h3>
              <p>{item.text}</p>
              <button>联系我们</button>
            </div>
          ))}
        </div>
      </section>
      <section className="cta-band">
        <div>
          <h2>准备好一起服务更多家庭了吗？</h2>
          <p>留下合作意向，我们会尽快与你联系。</p>
        </div>
        <button className="primary-button">
          提交合作意向
          <Handshake size={16} />
        </button>
      </section>
    </>
  );
}
