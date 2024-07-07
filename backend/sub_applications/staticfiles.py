from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.env import UploadConfig


def mount_staticfiles(app: FastAPI):
    """
    将一个目录中的静态文件提供为可通过 HTTP 访问的资源。具体来说，app.mount 方法将一个路径前缀与一个目录关联起来，使得该目录中的文件可以通过该路径前缀进行访问。
    将 files/upload_path 目录中的文件挂载到 /profile 路径前缀下

    e.g.:

    将 /profile URL 前缀下的所有请求映射到 files/upload_path 目录中的文件。例如：
    http://localhost:9099/dev-api/profile/some_file.txt 映射到 files/upload_path/some_file.txt
    http://localhost:9099/dev-api/profile/2024/07/05/demo_edf_20240705132949A605.edf 映射到 files/upload_path/2024/07/05/demo_edf_20240705132949A605.edf

    物理文件路径 files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf
    访问 URL：http://localhost:9099/dev-api/profile/upload/2024/07/05/demo_edf_20240705132949A605.edf
    这意味着当用户访问 URL 时，
    FastAPI 会返回存储在 files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf 的文件。
    """
    app.mount(f"{UploadConfig.UPLOAD_PREFIX}", StaticFiles(directory=f"{UploadConfig.UPLOAD_PATH}"), name="profile")
