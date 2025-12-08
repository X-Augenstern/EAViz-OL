from fastapi import APIRouter, Depends, Request
from os import path, remove
from sqlalchemy.orm import Session

from config.env import UploadConfig
from config.get_db import get_db
from module_admin.annotation.log_annotation import log_decorator
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.video_vo import VideoPageQueryModel, DeleteVideoModel, VideoModel, VideoUserPageQueryModel
from module_admin.service.common_service import CommonService
from module_admin.service.login_service import LoginService, CurrentUserModel
from module_admin.service.video_service import VideoService
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil

videoController = APIRouter(prefix="/system/video", dependencies=[Depends(LoginService.get_current_user)])


@videoController.get("/list", response_model=PageResponseModel,
                     dependencies=[Depends(CheckUserInterfaceAuth('system:video:list'))])
async def get_system_video_list(request: Request,
                                video_page_query: VideoPageQueryModel = Depends(VideoPageQueryModel.as_query),
                                query_db: Session = Depends(get_db),
                                current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取视频列表分页数据
    """
    try:
        video_page_query_result = VideoService.get_video_list_services(query_db, current_user.user.user_id,
                                                                       video_page_query, is_page=True)
        if video_page_query_result.rows:
            for row in video_page_query_result.rows:
                if isinstance(row, dict):
                    print("video_controller:get_system_video_list row is dict")
                    transform_video_path_2_url(request, row)
        logger.info('video_controller:get_system_video_list 获取成功')
        return ResponseUtil.success(model_content=video_page_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@videoController.get("/{video_id}", response_model=VideoModel,
                     dependencies=[Depends(CheckUserInterfaceAuth('system:video:query'))])
async def query_detail_system_video(request: Request, video_id: int, query_db: Session = Depends(get_db)):
    """
    根据Video的id获取Video详细信息
    """
    try:
        video_detail_result = VideoService.get_video_by_id_services(query_db, video_id)
        if isinstance(video_detail_result, dict):
            print("video_controller:query_detail_system_video video_detail_result is dict")
            transform_video_path_2_url(request, video_detail_result)
        logger.info(f'video_controller:query_detail_system_video 获取video_id 为{video_id}的信息成功')
        return ResponseUtil.success(data=video_detail_result.model_dump(by_alias=True))
    except Exception as e:
        return ResponseUtil.error(msg=str(e))


@videoController.get("/{user_id}", response_model=PageResponseModel,
                     dependencies=[Depends(CheckUserInterfaceAuth('system:video:query'))])
async def query_detail_system_video(request: Request, video_user_page_query: VideoUserPageQueryModel = Depends(
    VideoUserPageQueryModel.as_query), query_db: Session = Depends(get_db)):
    """
    根据用户的id获取Video详细信息
    """
    try:
        video_user_page_query_result = VideoService.get_video_list_by_user_id_services(query_db, video_user_page_query,
                                                                                       is_page=True)
        if video_user_page_query_result.rows:
            for row in video_user_page_query_result.rows:
                if isinstance(row, dict):
                    print("video_controller:query_detail_system_video row is dict")
                    transform_video_path_2_url(request, row)
        logger.info('video_controller:query_detail_system_video 获取成功')
        return ResponseUtil.success(model_content=video_user_page_query_result)
    except Exception as e:
        return ResponseUtil.error(msg=str(e))


@videoController.delete("/{video_ids}", dependencies=[Depends(CheckUserInterfaceAuth("system:video:remove"))])
@log_decorator(title='视频管理', business_type=3)
async def delete_system_video(request: Request, video_ids: str, query_db: Session = Depends(get_db),
                              current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    删除视频文件并从数据库中删除记录
    """
    if video_ids:
        video_id_list = video_ids.split(',')
        try:
            for video_id in video_id_list:
                video_detail_result = VideoService.get_video_by_id_services(query_db, int(video_id))
                if video_detail_result:
                    file_path = video_detail_result.video_path
                    if path.exists(file_path):
                        remove(file_path)
                        logger.info(f'video_controller:delete_system_video 文件 {file_path} 删除成功')
                    else:
                        logger.warning(f'video_controller:delete_system_video 文件 {file_path} 不存在或已被删除')
                else:
                    logger.warning(f'video_controller:delete_system_video Video ID {video_id} 未找到')

            delete_video = DeleteVideoModel(videoIds=video_ids)
            delete_video_result = VideoService.delete_video_services(query_db, delete_video)
            if delete_video_result.is_success:
                logger.info(f"video_controller:delete_system_video {delete_video_result.message}")
                return ResponseUtil.success(msg=delete_video_result.message)
            else:
                logger.warning(f"video_controller:delete_system_video {delete_video_result.message}")
                return ResponseUtil.failure(msg=delete_video_result.message)
        except Exception as e:
            logger.exception(e)
            return ResponseUtil.error(msg=str(e))
    else:
        return ResponseUtil.error(msg='传入Video ID为空')


def transform_video_path_2_url(request: Request, row: dict):
    """
    为每个视频添加可访问的URL
    """
    # rows是字典列表，字段名已转换为驼峰命名（video_path -> videoPath）
    video_path = row.get('videoPath')
    if video_path:
        row['videoUrl'] = CommonService.make_static_url(request, video_path, UploadConfig.DOWNLOAD_PATH)
        # 移除videoPath字段，避免暴露文件路径
        row.pop('videoPath', None)
