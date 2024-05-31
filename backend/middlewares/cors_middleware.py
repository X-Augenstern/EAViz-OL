from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI):
    # 前端页面url
    origins = [
        "http://localhost:80",
        "http://127.0.0.1:80",
    ]

    # 后台api允许跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # 只允许来自 http://localhost:80 和 http://127.0.0.1:80 前端页面的 URL 的跨域请求
        allow_credentials=True,  # 允许跨域请求携带凭证（如 Cookies）
        allow_methods=["*"],  # 允许所有 HTTP 方法（如 GET, POST, PUT, DELETE 等）
        allow_headers=["*"],  # 允许所有的 HTTP 头
    )
