import axios from 'axios'
import router from '../router'

// axios 实例：全局统一配置 baseURL / 超时时间
const service = axios.create({
  baseURL: 'http://127.0.0.1:8000', // 后端地址
  timeout: 5000
})

// 请求拦截器：每个请求发出前都会经过这里
// 作用：自动带上登录令牌，后端就能识别"是谁在请求"
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = token // 放进请求头，类比手动给每个请求加 header
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：每个响应回来都会经过这里
// 作用：401（未登录/令牌失效）时自动踢回登录页
service.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 令牌失效：清掉本地登录状态，跳登录页重新登录
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      router.push('/login')
    }
    return Promise.reject(error) // 把错误继续抛给调用处（页面里的 catch）
  }
)

export default service
