const useTagsViewStore = defineStore(
  'tags-view',
  {
    state: () => ({
      visitedViews: [],
      cachedViews: [],
      iframeViews: []
    }),
    actions: {
      // 添加视图
      addView(view) {
        this.addVisitedView(view)
        this.addCachedView(view)
      },
      addIframeView(view) {
        // 如果 iframeViews 数组中已经存在具有相同 path 的视图，则返回，不执行后续操作
        if (this.iframeViews.some(v => v.path === view.path)) return
        this.iframeViews.push(
          // Object.assign({}, view, {...})：
          // 新建空对象：
          //    创建一个新的空对象 {}。
          // 复制 view 的属性：
          //    将 view 对象的所有可枚举属性复制到新对象中。
          // 复制 {...} 的属性：
          //    将 {...} 对象的所有可枚举属性复制到新对象中。如果 {...} 中的属性名与 view 对象中的属性名相同，
          //    则这些属性会覆盖之前从 view 对象复制过来的属性。
          // 同时，新对象会包含一个 title 属性，其值为 view.meta.title，如果 view.meta.title 不存在，则使用默认值 'no-name'。
          Object.assign({}, view, {
            title: view.meta.title || 'no-name'
          })
        )
      },
      addVisitedView(view) {
        if (this.visitedViews.some(v => v.path === view.path)) return
        this.visitedViews.push(
          Object.assign({}, view, {
            title: view.meta.title || 'no-name'
          })
        )
      },
      addCachedView(view) {
        if (this.cachedViews.includes(view.name)) return
        if (!view.meta.noCache) {
          this.cachedViews.push(view.name)
        }
      },
      // 删除指定视图
      delView(view) {
        return new Promise(resolve => {
          this.delVisitedView(view)
          this.delCachedView(view)
          resolve({
            visitedViews: [...this.visitedViews],
            cachedViews: [...this.cachedViews]
          })
        })
      },
      delVisitedView(view) {
        return new Promise(resolve => {
          // 遍历 visitedViews 数组：
          // 使用 for...of 循环和 entries() 方法遍历 visitedViews 数组。entries() 方法返回一个包含数组中每个索引值和对应元素的数组。
          for (const [i, v] of this.visitedViews.entries()) {
            if (v.path === view.path) {
              this.visitedViews.splice(i, 1)  // 从数组的start索引位置开始删除deleteCount个元素。
              break
            }
          }
          this.iframeViews = this.iframeViews.filter(item => item.path !== view.path)
          resolve([...this.visitedViews])  // 使用展开运算符 ... 创建 visitedViews 数组的副本
        })
      },
      delIframeView(view) {
        return new Promise(resolve => {
          this.iframeViews = this.iframeViews.filter(item => item.path !== view.path)
          resolve([...this.iframeViews])
        })
      },
      delCachedView(view) {
        return new Promise(resolve => {
          const index = this.cachedViews.indexOf(view.name)
          // JavaScript 中一种简洁的写法，利用逻辑与 (&&) 运算符的特性来执行条件操作
          // 在 JavaScript 中，逻辑与运算符 (&&) 有“短路”特性：如果左侧的表达式为 false，则不会评估右侧的表达式。
          // 这意味着如果 index 为 -1（表示没有找到匹配项），右侧的 splice 语句将不会被执行。
          // 这种写法等价于以下更详细的条件语句：
          // if (index > -1) {
          //    this.cachedViews.splice(index, 1);
          // }
          index > -1 && this.cachedViews.splice(index, 1)
          resolve([...this.cachedViews])
        })
      },
      // 删除除指定视图外的其他视图
      delOthersViews(view) {
        return new Promise(resolve => {
          this.delOthersVisitedViews(view)
          this.delOthersCachedViews(view)
          resolve({
            visitedViews: [...this.visitedViews],
            cachedViews: [...this.cachedViews]
          })
        })
      },
      delOthersVisitedViews(view) {
        return new Promise(resolve => {
          this.visitedViews = this.visitedViews.filter(v => {
            return v.meta.affix || v.path === view.path
          })
          this.iframeViews = this.iframeViews.filter(item => item.path === view.path)
          resolve([...this.visitedViews])
        })
      },
      delOthersCachedViews(view) {
        return new Promise(resolve => {
          const index = this.cachedViews.indexOf(view.name)
          if (index > -1) {
            // slice 方法用于从一个数组中提取部分元素，返回一个新的数组，并且不会改变原数组。
            // array.slice(start, end) [)
            // start（可选）：开始提取元素的位置（包含该位置的元素）。如果未指定，则默认为 0。如果是负数，则表示从数组末尾开始的第几个元素。
            // end（可选）：停止提取元素的位置（不包含该位置的元素）。如果未指定，则提取到数组的末尾。如果是负数，则表示从数组末尾开始的第几个元素。

            // splice 方法用于添加或删除数组中的元素，会改变原数组。
            // array.splice(start, deleteCount, item1, item2, ...)
            // start：开始更改数组的位置（从 0 开始）。
            // deleteCount：要删除的元素数量。如果为 0，则不删除元素。
            // item1, item2, ...（可选）：要添加到数组中的元素。
            // eg：
            // let array = [1, 2, 3, 4, 5];
            // array.splice(2, 2, 'a', 'b');
            // console.log(array); // 输出: [1, 2, 'a', 'b', 5] 原数组被改变
            this.cachedViews = this.cachedViews.slice(index, index + 1)
          } else {
            this.cachedViews = []
          }
          resolve([...this.cachedViews])
        })
      },
      // 删除全部视图
      delAllViews(view) {
        return new Promise(resolve => {
          this.delAllVisitedViews(view)
          this.delAllCachedViews(view)
          resolve({
            visitedViews: [...this.visitedViews],
            cachedViews: [...this.cachedViews]
          })
        })
      },
      delAllVisitedViews(view) {
        return new Promise(resolve => {
          const affixTags = this.visitedViews.filter(tag => tag.meta.affix)
          this.visitedViews = affixTags
          this.iframeViews = []
          resolve([...this.visitedViews])
        })
      },
      delAllCachedViews(view) {
        return new Promise(resolve => {
          this.cachedViews = []
          resolve([...this.cachedViews])
        })
      },
      // 更新视图
      updateVisitedView(view) {
        // for (let v of this.visitedViews) {
        //   if (v.path === view.path) {
        //     v = Object.assign(v, view)
        //     break
        //   }
        // }
        let foundView = this.visitedViews.find(v => v.path === view.path);
        if (foundView) {
          Object.assign(foundView, view);  // 将 view 对象的属性合并到该对象中，并直接修改该对象的属性
        }
      },
      // 删除 visitedViews 数组中指定视图右侧的所有标签，同时更新 cachedViews 和 iframeViews 数组
      delRightTags(view) {
        return new Promise(resolve => {
          const index = this.visitedViews.findIndex(v => v.path === view.path)
          if (index === -1) {
            return
          }
          this.visitedViews = this.visitedViews.filter((item, idx) => {
            // 保留索引小于等于指定视图索引的标签，以及 meta.affix 为 true 的标签，不执行后续的删除代码
            if (idx <= index || (item.meta && item.meta.affix)) {
              return true
            }
            // 只有当上述条件为假时（即 idx < index 且 item.meta.affix 为 false），才会执行以下删除代码
            // 删除 cachedViews 中对应的缓存项
            const i = this.cachedViews.indexOf(item.name)
            if (i > -1) {
              this.cachedViews.splice(i, 1)
            }
            // 如果标签有 meta.link 属性，删除 iframeViews 中对应的项
            if (item.meta.link) {
              const fi = this.iframeViews.findIndex(v => v.path === item.path)
              this.iframeViews.splice(fi, 1)
            }
            return false
          })
          resolve([...this.visitedViews])
        })
      },
      // 删除 visitedViews 数组中指定视图左侧的所有标签，同时更新 cachedViews 和 iframeViews 数组
      delLeftTags(view) {
        return new Promise(resolve => {
          const index = this.visitedViews.findIndex(v => v.path === view.path)
          if (index === -1) {
            return
          }
          this.visitedViews = this.visitedViews.filter((item, idx) => {
            if (idx >= index || (item.meta && item.meta.affix)) {
              return true
            }
            const i = this.cachedViews.indexOf(item.name)
            if (i > -1) {
              this.cachedViews.splice(i, 1)
            }
            if (item.meta.link) {
              const fi = this.iframeViews.findIndex(v => v.path === item.path)
              this.iframeViews.splice(fi, 1)
            }
            return false
          })
          resolve([...this.visitedViews])
        })
      }
    }
  })

export default useTagsViewStore
