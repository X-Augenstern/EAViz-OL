from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config.env import UploadConfig


def mount_staticfiles(app: FastAPI):
    """
    将一个目录中的静态文件提供为可通过 HTTP 访问的资源。具体来说，app.mount 方法将一个路径前缀与一个目录关联起来，使得该目录中的文件可以通过该路径前缀进行访问。
    将 files/upload_path 目录中的文件挂载到 /profile 路径前缀下

    e.g.:

    将 /profile URL 前缀下的所有请求映射到 EAViz Files/upload_path 目录中的文件。例如：
    http://localhost:9099/dev-api/profile/some_file.txt 映射到 EAViz Files/upload_path/some_file.txt
    http://localhost:9099/dev-api/profile/2024/07/05/demo_edf_20240705132949A605.edf 映射到 EAViz Files/upload_path/2024/07/05/demo_edf_20240705132949A605.edf

    物理文件路径 EAViz Files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf
    访问 URL：http://localhost:9099/dev-api/profile/upload/2024/07/05/demo_edf_20240705132949A605.edf
    这意味着当用户访问 URL 时，
    FastAPI 会返回存储在 EAViz Files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf 的文件。
    """
    app.mount(
        f"{UploadConfig.UPLOAD_PREFIX}",
        StaticFiles(directory=f"{UploadConfig.UPLOAD_PATH}"),
        name="edf_files")

    """
    后端挂载：
        本地目录：EAViz Files/download_path（后端存放图片等静态文件的根目录）
        URL 对应关系：后端配置 URL前缀 /download 映射到本地目录 EAViz Files/download_path
        路径拼接逻辑：后端接收图片请求时，会截取 URL 中 /download/ 后的路径片段，与本地目录拼接，示例：
            若请求 URL 片段为 download/ESC_SD/SD/feature_map/feature_map.png，则实际访问本地文件：
            EAViz Files/download_path + /ESC_SD/SD/feature_map/feature_map.png
            
    前端 Vite Proxy 配置与核心原理：
        proxy：'/dev-api' - 'http://localhost:9099'
        Vite 代理不直接修改前端渲染的 src 字符串，而是通过拦截浏览器请求实现转发
        1. 浏览器向 “前端服务（http://localhost）” 发起请求，若请求路径含 /dev-api 前缀（如 /dev-api/xxx）；
        2. Vite Dev Server 拦截该请求，执行 rewrite 规则删除 /dev-api 前缀，得到纯路径 /xxx；
        3. 将处理后的请求转发到 target 配置的后端地址（http://localhost:9099/xxx）；
        4. 后端处理请求后，将响应结果返回给 Vite，再由 Vite 转发给浏览器。
        
    前端请求分析接口：
        1. 请求信息
            方法：POST
            前端请求地址：http://localhost/dev-api/eaviz/escsd（因前端端口 80，可省略 :80）
            请求参数：{ edfId: xxx, method: xxx, startTime: xxx, endTime: xxx }（从页面选择的分析参数）
        2. Vite 代理处理
            浏览器发起 http://localhost/dev-api/eaviz/escsd 请求
            → Vite 拦截后删除 /dev-api
            → 转发到后端：http://localhost:9099/eaviz/escsd
            → 后端接收并处理分析任务。
        
    后端处理完返回：
        后端构造图片 URL 数组（故意带 /dev-api 前缀，确保前端请求走 Vite 代理），返回给前端
        [
          "/dev-api/download/ESC_SD/SD/feature_map/feature_map.png",
          ...
        ]
        
    前端展示：
        1. 浏览器发起图片请求
            浏览器解析 src="/dev-api/download/..."，向 “前端服务（http://localhost）” 发起请求：
            http://localhost/dev-api/download/ESC_SD/SD/feature_map/feature_map.png
        2. Vite 代理再次转发
            Vite 拦截该请求，删除 /dev-api 前缀 → 得到路径 /download/ESC_SD/SD/feature_map/feature_map.png；
            转发到后端地址：http://localhost:9099/download/ESC_SD/SD/feature_map/feature_map.png。
        3. 后端返回图片资源
            后端根据 “/download 映射 EAViz Files/download_path” 规则，找到本地文件：
            EAViz Files/download_path/ESC_SD/SD/feature_map/feature_map.png
            读取文件并返回给浏览器，最终渲染在页面上。
    """
    app.mount(
        f"{UploadConfig.DOWNLOAD_PREFIX}",
        StaticFiles(directory=f"{UploadConfig.DOWNLOAD_PATH}"),
        name="analysis_res"
    )
