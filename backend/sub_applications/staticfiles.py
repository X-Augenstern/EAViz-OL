from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.env import UploadConfig


def mount_staticfiles(app: FastAPI):
    """
    挂载静态文件，将 URL 前缀 /profile 映射到服务器文件系统上的目录 eaviz/upload_path，当访问 URL 前缀时，FastAPI 会从该目录提供静态文件服务。（GET请求）
    """
    app.mount(f"{UploadConfig.UPLOAD_PREFIX}", StaticFiles(directory=f"{UploadConfig.UPLOAD_PATH}"), name="profile")
