// 全局公共配置
const AppConfig = {
  baseUrl: "http://127.0.0.1:8000/api/v1",
  tokenKey: "access_token"
}

// 统一请求封装（和页面原apiFetch逻辑保持完全一致）
async function apiRequest(path, options = {}) {
    const headers = { ...(options.headers || {}) };
    const token = localStorage.getItem(AppConfig.tokenKey);
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    // FormData上传文件不自动加json header
    if (!options.body || !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }
    const url = path;
    console.log("请求URL:", url);
    const res = await fetch(url, { ...options, headers });
    // 401跳转登录
    if (res.status === 401) {
      localStorage.removeItem(AppConfig.tokenKey);
      window.location.href = "login.html";
    }
    return res;
}
