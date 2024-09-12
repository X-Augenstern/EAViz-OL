<template>
  <div>
    <!-- <div class="pageHeaderContent">
      <div class="avatar">
        <a-avatar size="large" :src="currentUser.avatar" />
      </div>
      <div class="content">
        <div class="contentTitle">
          {{ getTime() }}好！{{ currentUser.name }}
        </div>
        <div>{{ currentUser.title }} |{{ currentUser.group }}</div>
      </div>
      <div class="extraContent">
        <div class="statItem">
          <a-statistic title="项目数" :value="56" />
        </div>
        <div class="statItem">
          <a-statistic title="团队内排名" :value="8" suffix="/ 24" />
        </div>
        <div class="statItem">
          <a-statistic title="项目访问" :value="2223" />
        </div>
      </div>
    </div> -->

    <div style="padding: 10px">
      <el-card>
        <!-- 使用div容器才能使flex布局生效 -->
        <div class="box">
          <!-- <img :src="userStore.avatar" class="avatar"> -->
          <el-avatar
            :size="100"
            :src="userStore.avatar"
            :style="{ marginLeft: '15px' }"
          ></el-avatar>
          <div class="bottom">
            <h3 class="title">{{ `${getTime()}好！${userStore.name}` }}</h3>
            <p class="subtitle">{{ title }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <div style="padding: 10px">
      <a-row :gutter="24">
        <a-col :xl="24" :lg="24" :md="24" :sm="24" :xs="24">
          <a-card
            class="projectList"
            :style="{ marginBottom: '24px' }"
            title="智能分析"
            :bordered="false"
            :loading="false"
            :body-style="{ padding: 0 }"
            :head-style="{ fontSize: '20px' }"
          >
            <!-- <template #extra>
              <a href=""> <span style="color: #1890ff">全部项目</span> </a>
            </template> -->
            <a-card-grid
              v-for="item in eavizItems"
              :key="item.id"
              class="projectGrid"
            >
              <a-card
                :body-style="{ padding: 0, fontSize: '16px' }"
                style="box-shadow: none"
                :bordered="false"
              >
                <a-card-meta :description="item.description" class="w-full">
                  <template #title>
                    <div class="cardTitle">
                      <a-avatar
                        :size="25"
                        :src="item.logo"
                        :style="{ backgroundColor: item.color }"
                      >
                        <!-- <span class="avatar-text">{{ item.logoTxt }}</span> -->
                      </a-avatar>
                      <!-- 
                      使用 <a :href="item.href"> 进行页面导航时，浏览器会进行完整的页面刷新，这意味着 Vue 应用将被完全重新加载。这个过程会导致所有的组件状态、Vuex 状态、以及任何未持久化的数据丢失。
                      为了避免这种情况，使用 Vue Router 提供的 <router-link> 组件进行导航。<router-link> 使用 Vue Router 的客户端路由机制，导航时不会刷新页面，从而保留应用的状态。
                      -->
                      <router-link :to="item.href" class="custom-link">
                        {{ item.title }}
                      </router-link>
                    </div>
                  </template>
                </a-card-meta>
                <div class="projectItemContent">
                  <a :href="item.memberLink">
                    {{ item.member || "" }}
                  </a>
                  <span class="datetime" ml-2 :title="item.updatedAt">
                    {{ item.updatedAt }}
                  </span>
                </div>
              </a-card>
            </a-card-grid>
          </a-card>
          <!-- <a-card :body-style="{ padding: 0 }" :bordered="false" class="activeCard" title="动态" :loading="false">
          <a-list :data-source="activities" class="activitiesList">
            <template #renderItem="{ item }">
              <a-list-item :key="item.id">
                <a-list-item-meta>
                  <template #title>
                    <span>
                      <a class="username">{{ item.user.name }}</a>&nbsp;
                      <span class="event">
                        <span>{{ item.template1 }}</span>&nbsp;
                        <a href="" style="color: #1890ff">
                          {{ item?.group?.name }} </a>&nbsp; <span>{{ item.template2 }}</span>&nbsp;
                        <a href="" style="color: #1890ff">
                          {{ item?.project?.name }}
                        </a>
                      </span>
                    </span>
                  </template>
                  <template #avatar>
                    <a-avatar :src="item.user.avatar" />
                  </template>
                  <template #description>
                    <span class="datetime" :title="item.updatedAt">
                      {{ item.updatedAt }}
                    </span>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card> -->
        </a-col>
        <!-- <a-col :xl="8" :lg="24" :md="24" :sm="24" :xs="24">
        <a-card :style="{ marginBottom: '24px' }" title="快速开始 / 便捷导航" :bordered="false" :body-style="{ padding: 0 }">
          <EditableLinkGroup />
        </a-card>
        <a-card :style="{ marginBottom: '24px' }" :bordered="false" title="XX 指数">
          <div class="chart">
            <div ref="radarContainer" />
          </div>
        </a-card>
        <a-card :body-style="{ paddingTop: '12px', paddingBottom: '12px' }" :bordered="false" title="团队">
          <div class="members">
            <a-row :gutter="48">
              <a-col v-for="item in projectNotice" :key="`members-item-${item.id}`" :span="12">
                <a :href="item.href">
                  <a-avatar :src="item.logo" size="small" />
                  <span class="member">{{ item.member }}</span>
                </a>
              </a-col>
            </a-row>
          </div>
        </a-card>
      </a-col> -->
      </a-row>
    </div>
  </div>
</template>

<script>
import {
  Statistic,
  Row,
  Col,
  Card,
  CardGrid,
  CardMeta,
  List,
  ListItem,
  ListItemMeta,
  Avatar,
} from "ant-design-vue";
import "ant-design-vue/dist/reset.css";
import { getTime } from "../../utils/time";

export default {
  components: {
    AStatistic: Statistic,
    ARow: Row,
    ACol: Col,
    ACard: Card,
    ACardGrid: CardGrid,
    ACardMeta: CardMeta,
    AList: List,
    AListItem: ListItem,
    AListItemMeta: ListItemMeta,
    AAvatar: Avatar,
  },
};
</script>


<script setup>
import { Radar } from "@antv/g2plot";
import EditableLinkGroup from "./editable-link-group.vue";
import useUserStore from "../../store/modules/user";
import { eavizItems } from "@/eaviz/config";
let userStore = useUserStore();
let title = import.meta.env.VITE_APP_TITLE;

defineOptions({
  name: "DashBoard",
});

// const currentUser = {
// avatar: userStore.avatar,
// name: userStore.name,
// userid: userStore.id,
// title: "交互专家",
// group: "蚂蚁金服－某某某事业群－某某平台部－某某技术部－UED",
// };

// const activities = [
//   {
//     id: "trend-1",
//     updatedAt: "几秒前",
//     user: {
//       name: "曲丽丽",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png",
//     },
//     group: {
//       name: "高逼格设计天团",
//       link: "http://github.com/",
//     },
//     project: {
//       name: "六月迭代",
//       link: "http://github.com/",
//     },
//     template1: "在",
//     template2: "新建项目",
//   },
//   {
//     id: "trend-2",
//     updatedAt: "几秒前",
//     user: {
//       name: "付小小",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/cnrhVkzwxjPwAaCfPbdc.png",
//     },
//     group: {
//       name: "高逼格设计天团",
//       link: "http://github.com/",
//     },
//     project: {
//       name: "六月迭代",
//       link: "http://github.com/",
//     },
//     template1: "在",
//     template2: "新建项目",
//   },
//   {
//     id: "trend-3",
//     updatedAt: "几秒前",
//     user: {
//       name: "林东东",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/gaOngJwsRYRaVAuXXcmB.png",
//     },
//     group: {
//       name: "中二少女团",
//       link: "http://github.com/",
//     },
//     project: {
//       name: "六月迭代",
//       link: "http://github.com/",
//     },
//     template1: "在",
//     template2: "新建项目",
//   },
//   {
//     id: "trend-4",
//     updatedAt: "几秒前",
//     user: {
//       name: "周星星",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/WhxKECPNujWoWEFNdnJE.png",
//     },
//     group: {
//       name: "5 月日常迭代",
//       link: "http://github.com/",
//     },
//     template1: "将",
//     template2: "更新至已发布状态",
//   },
//   {
//     id: "trend-5",
//     updatedAt: "几秒前",
//     user: {
//       name: "朱偏右",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/ubnKSIfAJTxIgXOKlciN.png",
//     },
//     group: {
//       name: "工程效能",
//       link: "http://github.com/",
//     },
//     project: {
//       name: "留言",
//       link: "http://github.com/",
//     },
//     template1: "在",
//     template2: "发布了",
//   },
//   {
//     id: "trend-6",
//     updatedAt: "几秒前",
//     user: {
//       name: "乐哥",
//       avatar:
//         "https://gw.alipayobjects.com/zos/rmsportal/jZUIxmJycoymBprLOUbT.png",
//     },
//     group: {
//       name: "程序员日常",
//       link: "http://github.com/",
//     },
//     project: {
//       name: "品牌迭代",
//       link: "http://github.com/",
//     },
//     template1: "在",
//     template2: "新建项目",
//   },
// ];

// const radarContainer = ref();
// const radarData = [
//   {
//     name: "个人",
//     label: "引用",
//     value: 10,
//   },
//   {
//     name: "个人",
//     label: "口碑",
//     value: 8,
//   },
//   {
//     name: "个人",
//     label: "产量",
//     value: 4,
//   },
//   {
//     name: "个人",
//     label: "贡献",
//     value: 5,
//   },
//   {
//     name: "个人",
//     label: "热度",
//     value: 7,
//   },
//   {
//     name: "团队",
//     label: "引用",
//     value: 3,
//   },
//   {
//     name: "团队",
//     label: "口碑",
//     value: 9,
//   },
//   {
//     name: "团队",
//     label: "产量",
//     value: 6,
//   },
//   {
//     name: "团队",
//     label: "贡献",
//     value: 3,
//   },
//   {
//     name: "团队",
//     label: "热度",
//     value: 1,
//   },
//   {
//     name: "部门",
//     label: "引用",
//     value: 4,
//   },
//   {
//     name: "部门",
//     label: "口碑",
//     value: 1,
//   },
//   {
//     name: "部门",
//     label: "产量",
//     value: 6,
//   },
//   {
//     name: "部门",
//     label: "贡献",
//     value: 5,
//   },
//   {
//     name: "部门",
//     label: "热度",
//     value: 7,
//   },
// ];
// let radar;
// onMounted(() => {
//   radar = new Radar(radarContainer.value, {
//     data: radarData,
//     xField: "label",
//     yField: "value",
//     seriesField: "name",
//     point: {
//       size: 4,
//     },
//     legend: {
//       layout: "horizontal",
//       position: "bottom",
//     },
//   });
//   radar.render();
// });

// onBeforeUnmount(() => {
//   radar?.destroy?.();
// });
</script>

<style scoped lang="less">
.box {
  display: flex;
  box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 12px;

  .bottom {
    margin-left: 20px;
    margin-top: 15px;

    .title {
      font-size: 25px;
      font-weight: 900;
      margin-bottom: 35px;
    }

    .subtitle {
      font-style: italic;
      color: royalblue;
      font-family: harmonyFont;
    }
  }
}

.textOverflow() {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  word-break: break-all;
}

// mixins for clearfix
// ------------------------
.clearfix() {
  zoom: 1;

  &::before,
  &::after {
    display: table;
    // content: " ";
  }

  &::after {
    clear: both;
    height: 0;
    font-size: 0;
    visibility: hidden;
  }
}

// .activitiesList {
//   padding: 0 24px 8px 24px;

//   .username {
//     color: rgba(0, 0, 0, 0.65);
//   }

//   .event {
//     font-weight: normal;
//   }
// }

// .pageHeaderContent {
//   display: flex;
//   padding: 12px;
//   margin-bottom: 24px;
//   box-shadow: rgba(0, 0, 0, 0.1) 0px 4px 12px;

//   .avatar {
//     flex: 0 1 72px;

//     &>span {
//       display: block;
//       width: 72px;
//       height: 72px;
//       border-radius: 72px;
//     }
//   }

//   .content {
//     position: relative;
//     top: 4px;
//     flex: 1 1 auto;
//     margin-left: 24px;
//     color: rgba(0, 0, 0, 0.45);
//     line-height: 22px;

//     .contentTitle {
//       margin-bottom: 12px;
//       color: rgba(0, 0, 0, 0.85);
//       font-weight: 500;
//       font-size: 20px;
//       line-height: 28px;
//     }
//   }
// }

// .extraContent {
//   .clearfix();

//   float: right;
//   white-space: nowrap;

//   .statItem {
//     position: relative;
//     display: inline-block;
//     padding: 0 32px;

//     >p:first-child {
//       margin-bottom: 4px;
//       color: rgba(0, 0, 0, 0.45);
//       font-size: 14px;
//       line-height: 22px;
//     }

//     >p {
//       margin: 0;
//       color: rgba(0, 0, 0, 0.85);
//       font-size: 30px;
//       line-height: 38px;

//       >span {
//         color: rgba(0, 0, 0, 0.45);
//         font-size: 20px;
//       }
//     }

//     &::after {
//       position: absolute;
//       top: 8px;
//       right: 0;
//       width: 1px;
//       height: 40px;
//       background-color: #e8e8e8;
//       // content: "";
//     }

//     &:last-child {
//       padding-right: 0;

//       &::after {
//         display: none;
//       }
//     }
//   }
// }

// .members {
//   a {
//     display: block;
//     height: 24px;
//     margin: 12px 0;
//     color: rgba(0, 0, 0, 0.65);
//     transition: all 0.3s;
//     .textOverflow();

//     .member {
//       margin-left: 12px;
//       font-size: 14px;
//       line-height: 24px;
//       vertical-align: top;
//     }

//     &:hover {
//       color: #1890ff;
//     }
//   }
// }

.projectList {
  :deep(.ant-card-meta-description) {
    height: 44px;
    overflow: hidden;
    color: rgba(0, 0, 0, 0.45);
    line-height: 22px;
  }

  .cardTitle {
    font-size: 0;

    .custom-link {
      display: inline-block;
      height: 24px;
      margin-left: 12px;
      color: rgba(0, 0, 0, 0.85);
      font-size: 18px;
      line-height: 24px;
      vertical-align: middle;

      &:hover {
        color: #1890ff;
      }
    }

    // .avatar-text {
    //   display: flex;
    //   align-items: center;
    //   justify-content: center;
    //   height: 100%;
    //   width: 100%;
    //   color: black;
    //   font-size: 18px;
    // }
  }

  .projectGrid {
    width: 33.33%;
  }

  .projectItemContent {
    display: flex;
    flex-basis: 100%;
    height: 20px;
    margin-top: 8px;
    overflow: hidden;
    font-size: 15px;
    line-height: 20px;
    .textOverflow();

    a {
      display: inline-block;
      flex: 1 1 0;
      color: rgba(0, 0, 0, 0.45);
      .textOverflow();

      &:hover {
        color: #1890ff;
      }
    }

    .datetime {
      flex: 0 0 auto;
      float: right;
      color: rgba(0, 0, 0, 0.25);
    }
  }
}

.datetime {
  color: rgba(0, 0, 0, 0.25);
}

// @media screen and (max-width: 1200px) and (min-width: 992px) {
//   .activeCard {
//     margin-bottom: 24px;
//   }

//   .members {
//     margin-bottom: 0;
//   }

//   .extraContent {
//     margin-left: -44px;

//     .statItem {
//       padding: 0 16px;
//     }
//   }
// }

// @media screen and (max-width: 992px) {
//   .activeCard {
//     margin-bottom: 24px;
//   }

//   .members {
//     margin-bottom: 0;
//   }

//   .extraContent {
//     float: none;
//     margin-right: 0;

//     .statItem {
//       padding: 0 16px;
//       text-align: left;

//       &::after {
//         display: none;
//       }
//     }
//   }
// }

@media screen and (max-width: 768px) {
  // .extraContent {
  //   margin-left: -16px;
  // }

  .projectList {
    .projectGrid {
      width: 50%;
    }
  }
}

// 在小屏幕设备（如手机）上调整布局，使页面内容更适合小屏幕显示
//@media screen and (max-width: 576px) {
//  .pageHeaderContent {
//    display: block;
//
//    .content {
//      margin-left: 0;
//    }
//  }
//
//  .extraContent {
//    .statItem {
//      float: none;
//    }
//  }
//}

@media screen and (max-width: 480px) {
  .projectList {
    .projectGrid {
      width: 100%;
    }
  }
}
</style>