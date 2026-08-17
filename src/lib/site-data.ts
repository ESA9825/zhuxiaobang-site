export type CaseItem = {
  slug: string;
  title: string;
  tags: string[];
  area: string;
  style: string;
  summary: string;
  image: string;
  details: string[];
};

export type TipItem = {
  slug: string;
  title: string;
  category: string;
  summary: string;
  image: string;
  steps: string[];
};

export type ReportItem = {
  slug: string;
  title: string;
  author: string;
  summary: string;
  image: string;
  highlights: string[];
};

export const navItems = [
  { href: "/", label: "首页" },
  { href: "/cases", label: "装修案例" },
  { href: "/decorate-tips", label: "装修锦囊" },
  { href: "/institute", label: "居住研究院" },
  { href: "/business", label: "业务合作" },
  { href: "/about", label: "关于我们" },
];

export const cases: CaseItem[] = [
  {
    slug: "90-cream-home",
    title: "90㎡ 奶油小家",
    tags: ["奶油风", "小户型", "旧房改造"],
    area: "90㎡",
    style: "奶油 · 温馨 · 自然",
    summary: "把原本昏暗的两居室改成通透的奶油系小家，用弧形、原木和柔光让日常更有温度。",
    image: "/images/case-1.jpg",
    details: [
      "玄关增加整面收纳柜，利用弧面弱化走廊转折。",
      "客餐一体布局，使用轻量沙发和圆桌释放活动空间。",
      "主卧用低饱和奶咖色墙漆，搭配原木床头和暖光吊灯。",
      "全屋无主灯设计，重点照明集中在阅读、用餐和玄关区域。",
    ],
  },
  {
    slug: "modern-three-bedroom",
    title: "现代三居的松弛感",
    tags: ["现代简约", "三居", "精装改造"],
    area: "126㎡",
    style: "简约 · 黑白 · 自然光",
    summary: "保留大面采光与开放格局，用克制配色和定制收纳让三居室显得更开阔。",
    image: "/images/case-2.jpg",
    details: [
      "客厅到阳台不做隔断，石材地台成为阅读与休憩的延伸。",
      "电视墙采用悬浮柜与隐形门，减少视觉碎片。",
      "餐厅使用岛台连接餐桌，形成完整洄游动线。",
      "卧室以低矮床背和分区灯光营造更安静的睡眠氛围。",
    ],
  },
  {
    slug: "warm-wooden-home",
    title: "原木日式温暖家",
    tags: ["日式", "原木", "亲子"],
    area: "110㎡",
    style: "原木 · 日式 · 简约",
    summary: "以原木、米白和棉麻材质为主，为一家三口打造有陪伴感的温暖住宅。",
    image: "/images/case-3.jpg",
    details: [
      "开放厨房搭配矮柜与吧台，方便照看孩子活动。",
      "儿童房使用可成长家具，预留阅读、游戏与收纳分区。",
      "全屋采用低饱和木饰面，减少高反光材质带来的冷感。",
      "阳台整合家政柜、洗手池与晾晒区，家务动线更短。",
    ],
  },
];

export const tips: TipItem[] = [
  {
    slug: "living-room-lighting",
    title: "客厅无主灯怎么布置才不暗",
    category: "灯光布局",
    summary: "从层高、灯具距离到重点照明，梳理客厅无主灯的 6 个关键步骤。",
    image: "/images/case-1.jpg",
    steps: [
      "先确认层高与梁位，避免灯具安装后形成压抑感。",
      "把基础照明、重点照明和氛围照明分开规划。",
      "筒灯距离墙面保持 35-50cm，防止洗墙光斑过强。",
      "沙发、餐桌、阅读角分别配置局部光源。",
      "色温统一在 3000-3500K，营造柔和连续的光环境。",
      "安装前用模拟图确认开关分组和回家模式。",
    ],
  },
  {
    slug: "kitchen-planning",
    title: "厨房动线这样排，做饭更顺手",
    category: "厨房设计",
    summary: "洗、切、炒、放四段动线怎么安排？从尺寸到高低台面一次讲清楚。",
    image: "/images/kitchen.jpg",
    steps: [
      "冰箱、水槽、备餐区、灶台依次形成连续操作流。",
      "操作台至少预留 60cm 备餐区，避免洗切挤在一起。",
      "洗菜盆靠窗，灶台避开窗扇，防止开窗碰水汽。",
      "高低台面相差 8-10cm，洗菜不弯腰、炒菜不架手。",
      "柜内按使用频率分层，把重物和电器放在顺手位置。",
    ],
  },
  {
    slug: "small-bedroom-storage",
    title: "小卧室收纳不够？这些位置还能再挖",
    category: "收纳规划",
    summary: "床尾、床头、飘窗和门后都是容易被忽略的小卧室收纳区。",
    image: "/images/case-3.jpg",
    steps: [
      "床尾做 35cm 薄柜，收纳次净衣和过季床品。",
      "床头用一体式背板整合插座、夜灯和随手物品。",
      "飘窗下做抽屉，上方保留休闲坐区。",
      "门后安装超薄洞洞板，收纳钥匙、帽子和常用包。",
      "衣柜内部优先挂区，再搭配少量抽屉和拉篮。",
    ],
  },
];

export const reports: ReportItem[] = [
  {
    slug: "2026-home-insight",
    title: "2026 家装趋势洞察白皮书",
    author: "住研数据组",
    summary: "从户型偏好、风格关键词到预算结构，观察新一代家庭的居住选择。",
    image: "/images/research.jpg",
    highlights: ["奶油与自然风持续增长", "小户型收纳成为核心诉求", "线下体验与线上决策并行"],
  },
  {
    slug: "kitchen-life-report",
    title: "厨房生活体验报告",
    author: "居住研究院",
    summary: "围绕做饭动线、厨房收纳和清洁负担，拆解理想厨房的真实问题。",
    image: "/images/kitchen.jpg",
    highlights: ["台面高度是高频痛点", "动线越短满意度越高", "嵌入式电器正在普及"],
  },
  {
    slug: "home-style-report",
    title: "家装风格观察报告",
    author: "设计趋势组",
    summary: "整理近三年风格关键词变化，帮助从业者理解用户审美迁移。",
    image: "/images/case-2.jpg",
    highlights: ["极简仍是主流基底", "材质质感优先于装饰", "个性化混搭比例上升"],
  },
];

export const toolItems = [
  {
    title: "户型改造",
    description: "输入户型信息，快速生成空间改造思路与拆改建议。",
    icon: "Layers",
  },
  {
    title: "装修预算",
    description: "按城市、面积和风格估算预算区间，规划每阶段花费。",
    icon: "Calculator",
  },
  {
    title: "风格测试",
    description: "通过偏好问答匹配适合的家居风格和参考案例。",
    icon: "Sparkles",
  },
  {
    title: "避坑清单",
    description: "把高频施工、主材和验收问题整理成可勾选清单。",
    icon: "ShieldCheck",
  },
];
