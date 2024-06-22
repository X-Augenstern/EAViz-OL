/**
 * sessionCache - 管理 sessionStorage 中的数据，当页面会话结束时（例如，关闭浏览器标签时）会清除：
 * set(key, value): 在 sessionStorage 中存储一个键值对。
 * get(key): 从 sessionStorage 中检索与键关联的值。
 * setJSON(key, jsonValue): 将 JavaScript 对象转换为 JSON 字符串并存储。
 * getJSON(key): 检索 JSON 字符串并将其解析回 JavaScript 对象。
 * remove(key): 从 sessionStorage 中移除与键相关的条目。
 */
const sessionCache = {
  set(key, value) {
    if (!sessionStorage) {
      return
    }
    if (key != null && value != null) {
      sessionStorage.setItem(key, value)
    }
  },
  get(key) {
    if (!sessionStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return sessionStorage.getItem(key)
  },
  setJSON(key, jsonValue) {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key) {
    const value = this.get(key)
    if (value != null) {
      return JSON.parse(value)
    }
  },
  remove(key) {
    sessionStorage.removeItem(key);
  }
}

/**
 * localCache - 管理 localStorage 中的数据，即使关闭浏览器后数据也会持久存在：
 * 其功能与 sessionCache 类似，但操作的是 localStorage，以确保数据在浏览器会话之间持久存储。
 */
const localCache = {
  set(key, value) {
    if (!localStorage) {
      return
    }
    if (key != null && value != null) {
      localStorage.setItem(key, value)
    }
  },
  get(key) {
    if (!localStorage) {
      return null
    }
    if (key == null) {
      return null
    }
    return localStorage.getItem(key)
  },
  setJSON(key, jsonValue) {
    if (jsonValue != null) {
      this.set(key, JSON.stringify(jsonValue))
    }
  },
  getJSON(key) {
    const value = this.get(key)
    if (value != null) {
      return JSON.parse(value)
    }
  },
  remove(key) {
    localStorage.removeItem(key);
  }
}

export default {
  /**
   * 会话级缓存
   */
  session: sessionCache,
  /**
   * 本地缓存
   */
  local: localCache
}
