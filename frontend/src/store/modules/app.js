import Cookies from 'js-cookie'

const useAppStore = defineStore(
  'app',
  {
    state: () => ({
      sidebar: {
        // 三元运算符，用来检查sidebarStatus是否存在：
        // Cookies.get('sidebarStatus')：如果sidebarStatus存在，结果为true
        // !!+Cookies.get('sidebarStatus')：如果sidebarStatus存在，使用+操作符将其转换为一个数字，然后用!!将这个数字转换为一个布尔值。
        // 这样，如果sidebarStatus的值是"1"，则结果为true，如果是"0"，则结果为false
        opened: Cookies.get('sidebarStatus') ? !!+Cookies.get('sidebarStatus') : true,
        withoutAnimation: false,
        hide: false
      },
      device: 'desktop',
      size: Cookies.get('size') || 'default'
    }),
    actions: {
      toggleSideBar(withoutAnimation) {
        if (this.sidebar.hide) {
          return false;
        }
        this.sidebar.opened = !this.sidebar.opened
        this.sidebar.withoutAnimation = withoutAnimation
        if (this.sidebar.opened) {
          Cookies.set('sidebarStatus', 1)
        } else {
          Cookies.set('sidebarStatus', 0)
        }
      },
      closeSideBar({ withoutAnimation }) {
        Cookies.set('sidebarStatus', 0)
        this.sidebar.opened = false
        this.sidebar.withoutAnimation = withoutAnimation
      },
      toggleDevice(device) {
        this.device = device
      },
      setSize(size) {
        this.size = size;
        Cookies.set('size', size)
      },
      toggleSideBarHide(status) {
        this.sidebar.hide = status
      }
    }
  })

export default useAppStore
