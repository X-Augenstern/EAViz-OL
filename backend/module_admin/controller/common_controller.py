from fastapi import APIRouter
from fastapi import Depends, File, Query
from module_admin.service.login_service import LoginService
from module_admin.service.common_service import *
from utils.response_util import *
from utils.log_util import *

commonController = APIRouter(prefix='/common', dependencies=[Depends(LoginService.get_current_user)])


@commonController.post("/upload")
async def common_upload(request: Request, file: UploadFile = File(...)):
    """
    将用户上传的文件保存到服务器的指定位置，并返回上传结果
    """
    try:
        upload_result = CommonService.upload_service(request, file)
        if upload_result.is_success:
            logger.info('上传成功')
            return ResponseUtil.success(model_content=upload_result.result)
        else:
            logger.warning('上传失败')
            return ResponseUtil.failure(msg=upload_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@commonController.get("/download")
async def common_download(request: Request, background_tasks: BackgroundTasks, file_name: str = Query(alias='fileName'),
                          delete: bool = Query()):
    """
    下载下载目录文件
    """
    try:
        download_result = CommonService.download_services(background_tasks, file_name, delete)
        if download_result.is_success:
            logger.info(download_result.message)
            return ResponseUtil.streaming(data=download_result.result)
        else:
            logger.warning(download_result.message)
            return ResponseUtil.failure(msg=download_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@commonController.get("/download/resource")
async def common_download(request: Request, resource: str = Query()):  # {resource}是路径参数 | resource: str = Query()是查询参数
    """
    下载上传目录文件
    """
    try:
        download_resource_result = CommonService.download_resource_services(resource)
        if download_resource_result.is_success:
            logger.info(download_resource_result.message)
            return ResponseUtil.streaming(data=download_resource_result.result)
        else:
            logger.warning(download_resource_result.message)
            return ResponseUtil.failure(msg=download_resource_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
