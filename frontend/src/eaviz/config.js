// 智能分析配置

/** 各个分析在eavizItems中的索引 */
export const eavizItemsIdx={
  escsd:0,
  ad:1,
  spid:2,
  srd:3,
  vd:4
}

/** 各个分析的详细信息 */
export const eavizItems = [
  {
    id: "01",
    title: "ESC + SD",
    color: '#40E0D0',  // instead logo
    description: "Epilepsy Syndrome Classification & Seizure Detection",
    // logoTxt: "E",
    href: "/eaviz/escsd",
    memberLink: "",
    methods: [
      {
        name: 'DSMN-ESS',
        description: "This method not only categorizes epilepsy syndromes but also allows for seizure detection"
      },
      {
        name: 'R3DClassifier',
        description: "This method can only categorize epilepsy syndromes"
      }
    ],
    span: 4
  },
  {
    id: "02",
    title: "AD",
    color: '#FFD700',
    description: "Artifact Detection",
    // logoTxt: "A",
    href: "/eaviz/ad",
    memberLink: "",
    // AD 支持的模型（需与后端 EAVizConfig.ModelConfig.AD_MODEL 保持一致）
    methods: [
      { name: 'Resnet34_AE_BCELoss', description: 'ResNet34 + AE, Binary Cross Entropy Loss' },
      { name: 'Resnet34_SkipAE_BCELoss', description: 'ResNet34 + SkipAE, Binary Cross Entropy Loss' },
      { name: 'Resnet34_MemAE_BCELoss', description: 'ResNet34 + MemAE, Binary Cross Entropy Loss' },
      { name: 'Resnet34_VAE_BCELoss', description: 'ResNet34 + VAE, Binary Cross Entropy Loss' },
      { name: 'SENet18_AE_BCELoss', description: 'SENet18 + AE, Binary Cross Entropy Loss' },
      { name: 'SENet18_SkipAE_BCELoss', description: 'SENet18 + SkipAE, Binary Cross Entropy Loss' },
      { name: 'SENet18_MemAE_BCELoss', description: 'SENet18 + MemAE, Binary Cross Entropy Loss' },
      { name: 'SENet18_VAE_BCELoss', description: 'SENet18 + VAE, Binary Cross Entropy Loss' },
      { name: 'VGG16_AE_BCELoss', description: 'VGG16 + AE, Binary Cross Entropy Loss' },
      { name: 'VGG16_SkipAE_BCELoss', description: 'VGG16 + SkipAE, Binary Cross Entropy Loss' },
      { name: 'VGG16_MemAE_BCELoss', description: 'VGG16 + MemAE, Binary Cross Entropy Loss' },
      { name: 'VGG16_VAE_BCELoss', description: 'VGG16 + VAE, Binary Cross Entropy Loss' },
      { name: 'DenseNet121_AE_BCELoss', description: 'DenseNet121 + AE, Binary Cross Entropy Loss' },
      { name: 'DenseNet121_SkipAE_BCELoss', description: 'DenseNet121 + SkipAE, Binary Cross Entropy Loss' },
      { name: 'DenseNet121_MemAE_BCELoss', description: 'DenseNet121 + MemAE, Binary Cross Entropy Loss' },
      { name: 'DenseNet121_VAE_BCELoss', description: 'DenseNet121 + VAE, Binary Cross Entropy Loss' },
    ],
    // AD 模型要求时间窗长度为 11s（见后端 AD_MODEL_DES）
    span: 11,
  },
  {
    id: "03",
    title: "SpiD",
    color: '#FF7F50',
    description: "Spike Detection",
    // logoTxt: "S",
    href: "/eaviz/spid",
    memberLink: "",
    methods: [
      {
        name: "Template Matching",
        description:
          "Sliding window template matching, time period can be arbitrarily selected, but the duration must be at least 0.3 s",
      },
      {
        name: "Unet+ResNet34",
        description:
          "Deep learning model, select start time and specify N segments of 30 seconds, total duration = N × 30 s",
      },
    ],
  },
  {
    id: "04",
    title: "SRD",
    color: '#EE82EE',
    description: "Spike Ripple Detection",
    // logoTxt: "H",
    href: "/eaviz/srd",
    memberLink: "",
    methods: [
      {
        name: "MKCNN",
        description: "Multi-Kernel Convolutional Neural Network for High-Frequency Oscillation detection",
      },
    ],
  },
  {
    id: "05",
    title: "VD",
    color: '#6495ED',
    description: "Video Detection",
    // logoTxt: "V",
    href: "/eaviz/vd",
    memberLink: "",
  },
  {
    id: "06",
    title: "智慧助手",
    color: '#90EE90',
    description: "Medical Assistant & Web Search",
    href: "/agent",
    memberLink: "",
  },
];
