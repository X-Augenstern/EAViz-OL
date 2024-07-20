import axios from 'axios'
import { ElNotification, ElMessageBox, ElMessage, ElLoading } from 'element-plus'
// ElMessageBox：显示模态对话框。
// ElMessage：显示临时消息。
// ElNotification：显示持续存在的通知。
import { getToken } from '@/utils/auth'
import errorCode from '@/utils/errorCode'
import { tansParams, blobValidate } from '@/utils/ruoyi'
import cache from '@/plugins/cache'
import { saveAs } from 'file-saver'
import useUserStore from '@/store/modules/user'

let downloadLoadingInstance;

// 是否显示重新登录对话框
export let isRelogin = { show: false };

axios.defaults.headers['Content-Type'] = 'application/json;charset=utf-8'

// 1、利用axios对象的create方法创建axios实例（用法同axios），并进行其他配置：基础路径、超时的时间
const service = axios.create({
  // axios中请求配置有baseURL选项，表示请求URL公共部分
  baseURL: import.meta.env.VITE_APP_BASE_API,
  // 超时
  timeout: 10000
})

// 2、axios实例添加请求拦截器：包含请求成功回调以及请求错误回调
service.interceptors.request.use(config => {
  // 是否需要设置 token
  /**
   * 检查请求配置 (config) 中是否有 isToken 属性，并且该属性是否被设置为 false。
   * 如果没有设置为 false 并且通过 getToken() 函数能够获取到令牌，
   * 那么它会在请求头 (config.headers) 中添加一个 Authorization 头，其值为 'Bearer ' + getToken()。
   * 这样，每个请求都会携带这个令牌，除非显式指定不需要令牌。
   */
  const isToken = (config.headers || {}).isToken === false
  if (getToken() && !isToken) {
    config.headers['Authorization'] = 'Bearer ' + getToken() // 让每个请求携带自定义token 请根据实际情况自行修改
  }

  // get请求映射params参数
  // 如果请求方法是 GET 并且有参数 (config.params)，则这段代码会将参数添加到 URL 中，并将参数对象清空。
  // 这是为了避免在 GET 请求中通过 URL 和参数对象同时传递参数。
  if (config.method === 'get' && config.params) {
    let url = config.url + '?' + tansParams(config.params);
    url = url.slice(0, -1);
    config.params = {};
    config.url = url;
  }

  // 是否需要防止数据重复提交
  const isRepeatSubmit = (config.headers || {}).repeatSubmit === false
  /**
   * 如果请求方法是 POST 或 PUT 并且没有设置 repeatSubmit 为 false，则执行防重复提交的逻辑。
   * 它会创建一个请求对象 (requestObj)，包括请求的 URL、数据和时间戳。
   * 然后，它会检查这个请求对象的大小，如果大于 5MB，则跳过防重复提交的检查。
   */
  if (!isRepeatSubmit && (config.method === 'post' || config.method === 'put')) {
    const requestObj = {
      url: config.url,
      data: typeof config.data === 'object' ? JSON.stringify(config.data) : config.data,
      time: new Date().getTime()
    }
    const requestSize = Object.keys(JSON.stringify(requestObj)).length; // 请求数据大小
    const limitSize = 5 * 1024 * 1024; // 限制存放数据5M
    if (requestSize >= limitSize) {
      console.warn(`[${config.url}]: ` + '请求数据大小超出允许的5M限制，无法进行防重复提交验证。')
      return config;
    }
    /**
     * 如果请求大小在限制之内，代码会从会话存储（假设是 cache.session）中获取名为 sessionObj 的之前的请求对象。
     * 如果当前请求与之前的请求在短时间间隔（这里设为 1000 毫秒）内内容完全相同，则视为重复提交，并且拒绝这个请求，返回一个错误。
     * 如果不是重复提交，就更新存储中的请求对象为当前请求。
     */
    const sessionObj = cache.session.getJSON('sessionObj')
    if (sessionObj === undefined || sessionObj === null || sessionObj === '') {
      cache.session.setJSON('sessionObj', requestObj)
    } else {
      const s_url = sessionObj.url;                // 请求地址
      const s_data = sessionObj.data;              // 请求数据
      const s_time = sessionObj.time;              // 请求时间
      const interval = 1000;                       // 间隔时间(ms)，小于此时间视为重复提交
      if (s_data === requestObj.data && requestObj.time - s_time < interval && s_url === requestObj.url) {
        const message = '数据正在处理，请勿重复提交';
        console.warn(`[${s_url}]: ` + message)
        return Promise.reject(new Error(message))
      } else {
        cache.session.setJSON('sessionObj', requestObj)
      }
    }
  }
  return config
}, error => {
  console.log(error)
  Promise.reject(error)
})

// 3、axios实例添加响应拦截器：包含成功回调以及失败回调
service.interceptors.response.use(res => {
  // 未设置状态码则默认成功状态
  const code = res.data.code || 200;
  // 获取错误信息
  const msg = errorCode[code] || res.data.msg || errorCode['default']
  // 打印响应数据类型和内容以帮助调试
  // console.log('Response type:', res.request.responseType);
  // console.log('Response data:', res.data);
  // 二进制数据则直接返回
  if (res.request.responseType === 'blob' || res.request.responseType === 'arraybuffer') {
    // Blob 和 ArrayBuffer 都是 JavaScript 中用于处理二进制数据的对象，但它们有一些关键区别和用途。以下是它们的主要区别：
    // Blob（Binary Large Object）表示一个不可变的、原始数据的类文件对象。它主要用于处理文件数据，可以通过JavaScript文件API进行读取和操作。
    //    适用场景:
    //    处理文件上传和下载。
    //    生成和操作文件对象，例如生成图像、视频、音频文件。
    //    读取方法: 可以使用 FileReader API 来读取 Blob 对象的内容，例如 readAsArrayBuffer、readAsText 和 readAsDataURL。
    // ArrayBuffer 表示通用的、固定长度的原始二进制数据缓冲区。它是数据缓冲区的底层对象，可以通过视图对象如 TypedArray（例如 Uint8Array、Float32Array 等）来操作实际数据。
    //    适用场景:
    //    处理原始二进制数据，例如从WebSockets、WebRTC或其他低级API接收到的二进制数据。
    //    高效的字节级操作，例如读取和修改二进制文件内容。
    //    读取方法: 通过视图对象（例如 Uint8Array、Float32Array）来操作 ArrayBuffer 的内容。
    // 选择合适的类型
    // 使用 Blob: 如果需要处理文件数据，例如上传文件或生成文件下载链接，应该使用 Blob。
    // 使用 ArrayBuffer: 如果需要对原始二进制数据进行高效的字节级操作，例如处理音频、视频或其他需要低级数据访问的场景，应该使用 ArrayBuffer。
    // 由于需要处理从后端发送过来的二进制 EEG 数据并将其绘制出来，使用 ArrayBuffer 更为合适，因为它可以方便地转换为 Float32Array 进行数据处理和绘制。
    return res.data
  }
  if (code === 401) {
    // 处理未授权或会话过期。如果未显示重新登录对话框，则显示对话框并提供重新登录或取消的选项。重新登录成功后，重定向到首页。
    if (!isRelogin.show) {
      isRelogin.show = true;
      /**
       * then 会在用户点击“重新登录”按钮后触发。这是因为当用户确认操作时，ElMessageBox.confirm 的 Promise 被解决（resolve）。
       * 此时，then 函数被调用，执行其中的代码。
       * 如果用户点击“取消”按钮，Promise 被拒绝（reject），并不会触发 then 中的代码。
       * 通常可以使用 catch 方法来处理这种情况，执行取消操作后需要的任何清理或其他逻辑。
       * 
       * 
       * Promise 本身不是异步请求，但它是一种用于处理异步操作的机制。
       * Promise 提供了一种结构化的方法来处理异步操作的结果，无论是成功完成还是失败。
       * 这使得编写异步代码（如网络请求、文件操作等）变得更加简洁和易于管理。
       * 
       * 1、状态管理：
       * Promise 对象有三种状态：pending（进行中）、fulfilled（已成功）和 rejected（已失败）。Promise 的状态一旦改变，就会保持这种状态，不会再变。
       * 
       * 2、构造函数：
       * 当创建一个 Promise 时，需要提供一个执行器函数（executor），这个函数接受两个参数：resolve 和 reject。
       * 这两个函数用于在异步操作成功时调用 resolve，或在操作失败时调用 reject。
       * resolve：
       *    当异步操作成功完成时调用这个函数。
       *    调用resolve会将Promise的状态从pending（未决）变为fulfilled（已兑现）。
       *    可以通过resolve传递任何值，这个值会被作为结果传递给Promise的后续处理方法（如then方法的第一个回调函数）。
       * reject：
       *    当异步操作失败或出现错误时调用这个函数。
       *    调用reject会将Promise的状态从pending（未决）变为rejected（已拒绝）。
       *    通常，你会传递一个错误或异常作为reject的参数，这个错误会被Promise的错误处理方法（如then的第二个参数或catch方法）捕获。
       * 
       * 3、处理结果：
       * Promise 提供了 then、catch 和 finally 等方法来处理异步操作的结果。
       * then 方法接受两个参数，都是可选的：
       *    第一个参数是一个函数，用来处理Promise被**解决（fulfilled）**的情况，即操作成功完成时调用。
       *    第二个参数也是一个函数，用来处理Promise被**拒绝（rejected）**的情况，即操作失败时调用。
       *    通常，then 主要用来处理成功的情况。例如，获取异步请求的数据、执行后续的异步操作等。
       *    当只关注成功的情况时，通常只提供then的第一个参数。
       * 
       * catch 方法
       *    catch 方法用于捕获Promise链中任何未被之前的then捕获的错误。
       *    它通常用于处理所有可能的错误情况，使得你可以在一个地方集中处理错误。
       *    catch 是专门用于处理拒绝（错误）情况的，使得错误处理更加清晰和专注。
       * 
       * eg：
       * new Promise((resolve, reject) => {
       *     // 模拟异步操作
       *     const success = true; // 可以改为 false 来模拟失败情况
       *     if (success) {
       *         resolve("Operation succeeded");
       *     } else {
       *         reject("Operation failed");
       *     }
       * })
       * .then(
       *     (result) => {
       *         console.log("Success:", result);
       *     },
       *     (error) => {
       *         console.error("Error:", error);
       *     }
       * );
       * 如果Promise被resolve（解决），则调用then的第一个参数，输出“Success: Operation succeeded”。
       * 如果Promise被reject（拒绝），则调用then的第二个参数，输出“Error: Operation failed”。
       */
      ElMessageBox.confirm('登录状态已过期，您可以继续留在该页面，或者重新登录', '系统提示', { confirmButtonText: '重新登录', cancelButtonText: '取消', type: 'warning' }).then(() => {
        isRelogin.show = false;
        useUserStore().logOut().then(() => {
          location.href = '/index';
        })
      }).catch(() => {
        isRelogin.show = false;
      });
    }
    return Promise.reject('无效的会话，或者会话已过期，请重新登录。')
  } else if (code === 500) {
    // 服务器错误，显示错误消息并拒绝承诺（Promise.reject）
    ElMessage({ message: msg, type: 'error' })
    return Promise.reject(new Error(msg))
  } else if (code === 601) {
    // 自定义错误处理，显示警告消息并拒绝承诺。
    ElMessage({ message: msg, type: 'warning' })
    return Promise.reject(new Error(msg))
  } else if (code !== 200) {
    // 其他错误，显示通知错误并拒绝承诺。
    ElNotification.error({ title: msg })
    return Promise.reject('error')
  } else {
    // 操作成功，返回响应数据。
    return Promise.resolve(res.data)
  }
},
  error => {
    console.log('err' + error)
    let { message } = error;
    if (message == "Network Error") {
      message = "后端接口连接异常";
    } else if (message.includes("timeout")) {
      message = "系统接口请求超时";
    } else if (message.includes("Request failed with status code")) {
      message = "系统接口" + message.substr(message.length - 3) + "异常";  // 从 message 字符串的倒数第三个字符开始提取直到字符串结束。这通常用来捕捉错误信息中的 HTTP 状态码
    }
    ElMessage({ message: message, type: 'error', duration: 5 * 1000 })
    return Promise.reject(error)
  }
)

// 通用下载方法：从服务器下载文件或处理服务器返回的数据
export function download(url, params, filename, config) {
  // 创建一个加载提示，通知用户正在下载数据。
  downloadLoadingInstance = ElLoading.service({ text: "正在下载数据，请稍候", background: "rgba(0, 0, 0, 0.7)", })
  return service.post(url, params, {
    // 请求发送之前，对 params 进行处理的函数。
    transformRequest: [(params) => { return tansParams(params) }],
    // 设置请求头为 'Content-Type': 'application/x-www-form-urlencoded'，表明发送的数据将以表单数据形式发送。
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    // 期望服务器响应的数据类型为二进制数据（如文件内容）。
    responseType: 'blob',
    // 将额外的配置参数合并到请求配置中
    ...config
  }).then(async (data) => {
    const isBlob = blobValidate(data);  // 检查响应数据是否为有效的 Blob 对象
    if (isBlob) {
      // 使用 Blob 构造函数创建一个 Blob 对象，并使用 saveAs 函数（通常来自 FileSaver 库）保存文件到本地
      const blob = new Blob([data])
      saveAs(blob, filename)
    } else {  // 尝试将响应数据转换为文本
      const resText = await data.text();
      const rspObj = JSON.parse(resText);
      const errMsg = errorCode[rspObj.code] || rspObj.msg || errorCode['default']
      ElMessage.error(errMsg);
    }
    downloadLoadingInstance.close();
  }).catch((r) => {
    console.error(r)
    ElMessage.error('下载文件出现错误，请联系管理员！')
    downloadLoadingInstance.close();
  })
}

export default service
