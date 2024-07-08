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
  // console.log(typeof time)  // string
  if (typeof time === 'object') {  // 如果是Date对象，则直接使用它
    date = time
  } else {
    if ((typeof time === 'string') && (/^[0-9]+$/.test(time))) {
      // 如果 time 参数是一个字符串且仅包含数字（即可能是一个时间戳），则将其转换为整数：
      //    /^[0-9]+$/ 是一个正则表达式，用于匹配一个或多个数字字符。
      //    ^ 表示字符串的开始。
      //    [0-9] 表示一个数字字符（0到9）。
      //    + 表示前面的模式 [0-9] 可以匹配一次或多次，即一个或多个数字字符。
      //    $ 表示字符串的结束。
      // .test(time) 方法用于测试字符串 time 是否匹配正则表达式模式。如果匹配，则返回 true；否则，返回 false。
      time = parseInt(time)
    } else if (typeof time === 'string') {
      // 如果 time 参数是一个字符串，则进行以下转换：
      //    new RegExp(/-/gm) 创建了一个正则表达式，用于匹配所有的 - 字符。
      //    replace(new RegExp(/-/gm), '/') 将字符串中的所有 - 替换为 /。
      //    g 标志表示全局匹配（替换所有的匹配项）。
      //    m 标志表示多行匹配，表示 ^ 和 $ 可以匹配每行的开始和结束，而不仅仅是整个输入字符串的开始和结束。(但在这里并不影响结果，因为日期字符串通常是一行的。)
      //    这一步将 T 替换为空格，主要用于处理 ISO 8601 格式的日期时间字符串，如 "2023-01-01T12:00:00"，使其变成 "2023-01-01 12:00:00"。
      //    replace 方法默认只替换第一个匹配项，但由于日期时间字符串中通常只有一个 T，所以这里不需要全局匹配。
      //    new RegExp(/\.[\d]{3}/gm) 创建了一个正则表达式，用于匹配 . 后面紧跟三个数字的部分（即毫秒部分，如 .123）。

      // []（字符类）
      //    方括号 [] 用于定义一个字符类，表示在这个位置可以匹配的任意一个字符。
      //    [0-9] 表示任意一个数字字符（0 到 9）。
      //    [a-z] 表示任意一个小写字母字符（a 到 z）。
      //    [A-Z] 表示任意一个大写字母字符（A 到 Z）。
      //    [abc] 表示字符 a、b 或 c 之一。
      //    [\d] 是一个字符类，表示任意一个数字字符。这里的 \d 是预定义字符类，等价于 [0-9]。

      // {}（量词）
      //    花括号 {} 用于指定前一个字符或子表达式的匹配次数。
      //    {n} 表示恰好匹配 n 次。
      //    {n,} 表示至少匹配 n 次。
      //    {n,m} 表示匹配 n 到 m 次。
      time = time.replace(new RegExp(/-/gm), '/').replace('T', ' ').replace(new RegExp(/\.[\d]{3}/gm), '');
      // "2023-01-01T12:00:00.123" -> 最终结果是 "2023/01/01 12:00:00"，这是一个可以被 JavaScript Date 对象正确解析的日期时间字符串。
    }
    // 如果 time 参数是一个数字且长度为 10（秒级时间戳），则将其转换为毫秒级时间戳。
    if ((typeof time === 'number') && (time.toString().length === 10)) {
      time = time * 1000
    }

    date = new Date(time)
  }
  const formatObj = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,  // 月（注意：月份从0开始，所以要加1）
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay()         // 星期几（0是周日）
  }
  // 使用正则表达式替换格式字符串中的占位符。
  // {y|m|d|h|i|s|a} 会匹配模式中的任何一个占位符。
  // .replace(/{(y|m|d|h|i|s|a)+}/g, (result, key) => { ... }) 使用正则表达式匹配 format 字符串中的占位符，并用回调函数的返回值替换它们。
  // /{(y|m|d|h|i|s|a)+}/g：
  //    / 和 / 之间是正则表达式的主体。
  //    { 和 } 是占位符的包围符号。
  //    括号 () 定义了一个捕获组，| 表示“或”的关系。(y|m|d|h|i|s|a) 用于匹配单个字符 y, m, d, h, i, s, a。
  //    {} 包围了整个捕获组，用于在模板字符串中表示占位符。例如，{y} 表示年份占位符，{m} 表示月份占位符，依此类推。
  //    + 表示匹配一个或多个前面的字符（即捕获组中的一个字符）。
  //    g 标志表示全局匹配，即匹配字符串中的所有符合条件的部分。
  // result 是匹配到的完整字符串，例如 {y}。
  // key 是捕获组匹配的内容，即 y, m, d, h, i, s, a 其中之一。
  const time_str = format.replace(/{(y|m|d|h|i|s|a)+}/g, (result, key) => {
    let value = formatObj[key]
    // Note: getDay() returns 0 on Sunday
    // 如果是星期几的占位符 'a'，则将其转换为中文的星期几。
    if (key === 'a') { return ['日', '一', '二', '三', '四', '五', '六'][value] }
    // 如果占位符长度大于 0 且值小于 10，则在值前面加 '0' 以补齐两位数。
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
