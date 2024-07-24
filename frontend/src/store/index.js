// 引入pinia仓库
import { createPinia } from 'pinia'
// 创建pinia
const store = createPinia()

// doc 3
store.use(({ store }) => {
  const initialState = JSON.parse(JSON.stringify(store.$state));

  store.$reset = () => {
    store.$patch(initialState);
  }
})

export default store