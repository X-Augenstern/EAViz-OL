/**
 * 通用js方法封装处理
 * Copyright (c) 2019
 */

// 日期格式化
export function parseTime(time, pattern) {
  if (arguments.length === 0 || !time) {
    return null
  }
  const format = pattern || '{y}-{m}-{d} {h}:{i}:{s}'
  let date
  if (typeof time === 'object') {
    date = time
  } else {
    if ((typeof time === 'string') && (/^[0-9]+$/.test(time))) {
      time = parseInt(time)
    } else if (typeof time === 'string') {
      time = time.replace(new RegExp(/-/gm), '/').replace('T', ' ').replace(new RegExp(/\.[\d]{3}/gm), '');
    }
    if ((typeof time === 'number') && (time.toString().length === 10)) {
      time = time * 1000
    }
    date = new Date(time)
  }
  const formatObj = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay()
  }
  const time_str = format.replace(/{(y|m|d|h|i|s|a)+}/g, (result, key) => {
    let value = formatObj[key]
    // Note: getDay() returns 0 on Sunday
    if (key === 'a') { return ['日', '一', '二', '三', '四', '五', '六'][value] }
    if (result.length > 0 && value < 10) {
      value = '0' + value
    }
    return value || 0
  })
  return time_str
}

// 表单重置
export function resetForm(refName) {
  if (this.$refs[refName]) {
    this.$refs[refName].resetFields();
  }
}

// 添加日期范围
export function addDateRange(params, dateRange, propName) {
  let search = params;
  dateRange = Array.isArray(dateRange) ? dateRange : [];
  if (typeof (propName) === 'undefined') {
    search['beginTime'] = dateRange[0];
    search['endTime'] = dateRange[1];
  } else {
    search['begin' + propName] = dateRange[0];
    search['end' + propName] = dateRange[1];
  }
  return search;
}

// 回显数据字典
export function selectDictLabel(datas, value) {
  if (value === undefined) {
    return "";
  }
  var actions = [];
  Object.keys(datas).some((key) => {
    if (datas[key].value == ('' + value)) {
      actions.push(datas[key].label);
      return true;
    }
  })
  if (actions.length === 0) {
    actions.push(value);
  }
  return actions.join('');
}

// 回显数据字典（字符串数组）
export function selectDictLabels(datas, value, separator) {
  if (value === undefined || value.length === 0) {
    return "";
  }
  if (Array.isArray(value)) {
    value = value.join(",");
  }
  var actions = [];
  var currentSeparator = undefined === separator ? "," : separator;
  var temp = value.split(currentSeparator);
  Object.keys(value.split(currentSeparator)).some((val) => {
    var match = false;
    Object.keys(datas).some((key) => {
      if (datas[key].value == ('' + temp[val])) {
        actions.push(datas[key].label + currentSeparator);
        match = true;
      }
    })
    if (!match) {
      actions.push(temp[val] + currentSeparator);
    }
  })
  return actions.join('').substring(0, actions.join('').length - 1);
}

// 字符串格式化(%s )
export function sprintf(str) {
  var args = arguments, flag = true, i = 1;
  str = str.replace(/%s/g, function () {
    var arg = args[i++];
    if (typeof arg === 'undefined') {
      flag = false;
      return '';
    }
    return arg;
  });
  return flag ? str : '';
}

// 转换字符串，undefined,null等转化为""
export function parseStrEmpty(str) {
  if (!str || str == "undefined" || str == "null") {
    return "";
  }
  return str;
}

// 数据合并
export function mergeRecursive(source, target) {
  for (var p in target) {
    try {
      if (target[p].constructor == Object) {
        source[p] = mergeRecursive(source[p], target[p]);
      } else {
        source[p] = target[p];
      }
    } catch (e) {
      source[p] = target[p];
    }
  }
  return source;
};

/**
 * 构造树型结构数据
 * @param {*} data 数据源
 * @param {*} id id字段 默认 'id'
 * @param {*} parentId 父节点字段 默认 'parentId'
 * @param {*} children 孩子节点字段 默认 'children'
 */
export function handleTree(data, id, parentId, children) {
  let config = {
    id: id || 'id',
    parentId: parentId || 'parentId',
    childrenList: children || 'children'
  };

  var childrenListMap = {};
  var nodeIds = {};
  var tree = [];

  for (let d of data) {
    let parentId = d[config.parentId];
    if (childrenListMap[parentId] == null) {
      childrenListMap[parentId] = [];
    }
    nodeIds[d[config.id]] = d;
    childrenListMap[parentId].push(d);
  }

  for (let d of data) {
    let parentId = d[config.parentId];
    if (nodeIds[parentId] == null) {
      tree.push(d);
    }
  }

  for (let t of tree) {
    adaptToChildrenList(t);
  }

  function adaptToChildrenList(o) {
    if (childrenListMap[o[config.id]] !== null) {
      o[config.childrenList] = childrenListMap[o[config.id]];
    }
    if (o[config.childrenList]) {
      for (let c of o[config.childrenList]) {
        adaptToChildrenList(c);
      }
    }
  }
  return tree;
}

/**
* 参数处理
* @param {*} params  参数
* 将一个 JavaScript 对象转换成一个 URL 编码的查询字符串。
* 这种格式通常用于 HTTP GET 请求中的查询参数或用于 POST 请求时以 application/x-www-form-urlencoded MIME 类型发送数据。
*/
export function tansParams(params) {
  /**
   * eg：
   * {
   * name: "John",
   * age: 30,
   * details: {
   *   role: "admin",
   *   active: true
   *  }
   * }
   * -> name=John&age=30&details%5Brole%5D=admin&details%5Bactive%5D=true&  details[role]
   * %5B 和 %5D 分别是 [ 和 ] 的 URL 编码。这样的字符串可以直接用在 URL 的查询部分或作为 application/x-www-form-urlencoded 类型的 POST 请求体。
   */
  let result = ''
  for (const propName of Object.keys(params)) {  // 获取所有键名
    const value = params[propName];
    var part = encodeURIComponent(propName) + "=";  // 对于每个属性名（propName），编码属性名并添加等号 = 准备接收对应的值
    if (value !== null && value !== "" && typeof (value) !== "undefined") {
      if (typeof value === 'object') {
        for (const key of Object.keys(value)) {
          if (value[key] !== null && value[key] !== "" && typeof (value[key]) !== 'undefined') {
            let params = propName + '[' + key + ']';
            var subPart = encodeURIComponent(params) + "=";
            result += subPart + encodeURIComponent(value[key]) + "&";
          }
        }
      } else {
        result += part + encodeURIComponent(value) + "&";
      }
    }
  }
  return result
}

/**
 * 返回规范后的项目路径
 */
export function getNormalPath(p) {
  /* ===（严格相等）
  类型和值都相等：=== 运算符首先会检查两个操作数的类型，如果类型不同，则返回 false。如果类型相同，再检查它们的值是否相等。
  不进行类型转换：=== 不会进行任何类型转换，只会在类型和值都相等的情况下返回 true。
  
     ==（宽松相等）
  值相等：== 运算符会在比较前进行类型转换（如果类型不同），然后再检查它们的值是否相等。
  进行类型转换：== 会将不同类型的操作数转换为相同类型，然后再进行比较。这可能会导致一些意想不到的结果。
  console.log(1 == '1');         // true, 因为在比较前，字符串 '1' 被转换成了数字 1
  console.log(true == 1);        // true, 因为在比较前，布尔值 true 被转换成了数字 1
  console.log(null == undefined);  // true, 因为在宽松比较中，null 和 undefined 被认为相等
  console.log('' == false);      // true, 因为在比较前，空字符串 '' 被转换成了布尔值 false
  console.log([1, 2] == '1,2');  // true, 因为在比较前，数组被转换成了字符串 '1,2'

  在实际开发中，推荐使用 ===，以确保比较的准确性和代码的可读性。只有在明确知道需要进行类型转换的情况下，才使用 ==。
  */
  if (p.length === 0 || !p || p == 'undefined') {
    return p
  };
  let res = p.replace('//', '/')  // 双斜杠 // 替换为单斜杠 /
  if (res[res.length - 1] === '/') {
    return res.slice(0, res.length - 1)  // 移除路径末尾的斜杠
  }
  return res;
}

/**
 * 验证是否为blob格式
 * 函数通过访问 data.type 来获取 Blob 对象的 MIME 类型。
 * 判断该 MIME 类型是否与 'application/json' 不同。
 * 如果不同，说明 Blob 对象可能包含非 JSON 的内容，如二进制文件数据（如图片、PDF等），因此返回 true。
 * 如果相同，说明 Blob 对象包含的是 JSON 格式的文本数据，因此返回 false。
 * 
 * MIME 类型（Multipurpose Internet Mail Extensions，多用途互联网邮件扩展类型）是一种标准，用于描述文档的内容类型。
 * 这个标准最初是为了解决电子邮件中二进制文件传输的问题而开发的，但随着时间的发展，它也被广泛用于描述通过互联网传输的其他文件和数据的类型。
 * MIME 类型通常包括两部分，用斜杠 / 分隔：
 *    类型（Type）：这是主类型，描述数据的大类，如 text、image、application 等。
 *    子类型（Subtype）：这是具体的格式，用于进一步描述文件的具体格式，如 text/plain、image/jpeg、application/json 等。
 * 
 * 一些常见的 MIME 类型包括：
 * 文本文件：text/plain、text/html、text/css、text/javascript * 
 * 图片文件：image/jpeg、image/png、image/gif
 * 视频文件：video/mp4、video/quicktime
 * 音频文件：audio/mpeg、audio/ogg
 * 应用程序特定文件：application/json（用于JSON格式数据）、application/pdf（PDF文件）、application/zip（ZIP压缩文件）
 */
export function blobValidate(data) {
  return data.type !== 'application/json'
}
