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
    methods:[
      {
        name:'DSMN-ESS',
        description:"This method not only categorizes epilepsy syndromes but also allows for seizure detection"
      },
      {
        name:'R3DClassifier',
        description:"This method can only categorize epilepsy syndromes"
      }
    ],
    span:4
  },
  {
    id: "02",
    title: "AD",
    color: '#7FFF00',
    description: "Artifact Detection",
    // logoTxt: "A",
    href: "/eaviz/ad",
    memberLink: "",
  },
  {
    id: "03",
    title: "SpiD",
    color: '#FF7F50',
    description: "Spike Detection",
    // logoTxt: "S",
    href: "/eaviz/spid",
    memberLink: "",
  },
  {
    id: "04",
    title: "SRD",
    color: '#EE82EE',
    description: "Spike Ripple Detection",
    // logoTxt: "H",
    href: "/eaviz/srd",
    memberLink: "",
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
    title: "",
    description: "To be added",
    href: "",
    memberLink: "",
  },
];
