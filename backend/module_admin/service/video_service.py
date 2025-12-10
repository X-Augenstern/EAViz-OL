from datetime import timedelta, timezone
from json import dumps
from os import path, makedirs, rename
from shutil import move
from starlette.requests import Request

from config.env import EAVizConfig, UploadConfig, RedisConfig, RedisInitKeyConfig
from module_admin.dao.video_dao import *
from module_admin.entity.vo.common_vo import CrudResponseModel, UploadResponseModel
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.upload_util import UploadUtil


class VideoService:
    """
    视频管理模块服务层
    """

    @classmethod
    def get_video_by_id_services(cls, query_db: Session, video_id: int):
        """
        根据video的id获取video信息service
        """
        video_res = VideoDao.get_video_by_id(query_db, video_id)
        return VideoModel(**CamelCaseUtil.transform_result(video_res))

    @classmethod
    def get_video_list_services(cls, query_db: Session, user_id: int, query_object: VideoPageQueryModel,
                                is_page: bool = False):
        """
        获取video信息service
        """
        video_list_result = VideoDao.get_video_list(query_db, user_id, query_object, is_page)
        return video_list_result

    @classmethod
    def get_video_list_by_user_id_services(cls, query_db: Session, page_object: VideoUserPageQueryModel,
                                           is_page: bool = False):
        """
        根据用户id获取用户拥有的Video列表信息Service
        """
        video_user_list = VideoDao.get_video_list_by_user_id(query_db, page_object, is_page)
        return video_user_list

    @classmethod
    def add_video_services(cls, query_db: Session, page_object: AddVideoModel):
        """
        新增Video信息并返回新增的video_id service
        """
        result = dict(is_success=True, message='', result=None)
        messages = []
        added_ids = []
        try:
            for video in page_object.video_list:
                added_video = VideoDao.add_video_dao(query_db, video)
                if not added_video:
                    result['is_success'] = False
                    messages.append(f'{video.video_name} 已存在')
                else:
                    # db.flush() 后 ORM 会在同一事务里拿到自增的 video_id 并回填到 added_video，不需要再额外查库
                    VideoDao.add_video_user_dao(query_db, VideoUserModel(videoId=added_video.video_id,
                                                                         userId=page_object.user_id))
                    messages.append(f'{video.video_name} 添加成功')
                    added_ids.append(added_video.video_id)
            query_db.commit()
        except Exception as e:
            query_db.rollback()
            raise e

        result['message'] = ';'.join(messages)
        result['result'] = dict(video_ids=added_ids) if added_ids else None
        return CrudResponseModel(**result)

    @classmethod
    def delete_video_services(cls, query_db: Session, page_object: DeleteVideoModel):
        """
        删除Video信息Service
        """
        result = dict(is_success=True, message='删除成功')
        if page_object.video_ids:
            video_id_list = page_object.video_ids.split(',')
            try:
                for video_id in video_id_list:
                    video_id_dict = dict(videoId=video_id)
                    VideoDao.delete_video_dao(query_db, VideoModel(**video_id_dict))
                    VideoDao.delete_video_user_dao(query_db, VideoUserModel(**video_id_dict))
                query_db.commit()
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result['is_success'] = False
            result['message'] = '传入Video ID为空'
        return CrudResponseModel(**result)

    @classmethod
    def save_processed_video_services(cls, processed_video_path: str, original_filename: str,
                                      save_path: str = EAVizConfig.AddressConfig.get_vd_adr("res")):
        """
        保存处理后的视频文件到指定目录（默认 VD/res），使用类似EDF的命名规则
        :param processed_video_path: 处理后的视频文件路径（VD/res目录中的临时文件）
        :param original_filename: 原始文件名（用于生成新文件名）
        :param save_path: 保存目录
        :return: 上传结果
        """
        if not path.exists(processed_video_path):
            return CrudResponseModel(is_success=False, message=f'处理后的视频文件不存在: {processed_video_path}')

        try:
            makedirs(save_path, exist_ok=True)
        except Exception as e:
            logger.error(f'创建VD/res目录失败: {save_path}, 错误: {str(e)}')
            return CrudResponseModel(is_success=False, message=f'创建VD/res目录失败: {str(e)}')

        # 获取原文件扩展名，如果没有则使用.mp4
        original_ext = original_filename.rsplit('.', 1)[-1] if '.' in original_filename else 'mp4'
        relative_path = (f'{datetime.now().strftime("%Y")}/'
                         f'{datetime.now().strftime("%m")}/'
                         f'{datetime.now().strftime("%d")}')
        dir_path = path.join(save_path, relative_path)
        try:
            makedirs(dir_path)
        except FileExistsError:
            pass
        # demo_20240705132949A605.mp4（类似EDF的命名规则）
        filename = (f'{original_filename.rsplit(".", 1)[0]}_'
                    f'{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    f'{UploadConfig.UPLOAD_MACHINE}'
                    f'{UploadUtil.generate_random_number()}.'
                    f'{original_ext}')
        # EAViz Files/download_path/VD/res/demo_20240705132949A605.mp4
        filepath = path.join(dir_path, filename)

        try:
            # 将处理后的视频文件重命名（如果文件已经在VD/res目录，则重命名；否则移动）
            if path.dirname(path.abspath(processed_video_path)) == path.abspath(dir_path):
                # 如果文件已经在VD/res目录，直接重命名
                rename(processed_video_path, filepath)
            else:
                # 否则移动文件
                move(processed_video_path, filepath)
            logger.info(f'处理后的视频文件已保存: {filepath}, 原始文件名: {original_filename}')
        except Exception as e:
            logger.error(f'保存处理后的视频文件失败: {processed_video_path} -> {filepath}, 错误: {str(e)}')
            return CrudResponseModel(is_success=False, message=f'保存视频文件失败: {str(e)}')

        result = CrudResponseModel(
            is_success=True,
            result=UploadResponseModel(
                # 文件名（用于URL生成）
                fileName=filename,
                # demo_20240705132949A605.mp4
                newFileName=filename,
                # demo.mp4（原文件名，用于数据库保存）
                originalFilename=original_filename,
                filePath=filepath,
                extraInfo=None
            ),
            message=f'{original_filename} 保存成功'
        )
        return result

    @classmethod
    async def cache_processed_video_services(cls, request: Request, output_path: str, output_url: str,
                                             original_name: str, video_id: int):
        """
        将处理后的视频写入Redis，方便后续定期清理
        """
        redis_client = getattr(request.app.state, "redis", None)
        if not redis_client or not output_path:
            return

        key = f"{RedisInitKeyConfig.VIDEO_CLEANUP.get('key')}:{video_id}"
        expire_at = (datetime.now(timezone.utc) + timedelta(seconds=RedisConfig.video_file_ttl_seconds)).isoformat()
        payload = {
            "path": output_path,
            "output_url": output_url,
            "video_name": original_name,
            "expire_at": expire_at,
            "video_id": video_id
        }
        try:
            ttl_seconds = RedisConfig.redis_key_ttl_seconds
            await redis_client.delete(key)  # 缓存时先删除旧Key，再设置新Key（避免重复）
            await redis_client.set(key, dumps(payload), ex=ttl_seconds)
            logger.info(f"已缓存处理后视频到Redis, key={key}, ttl={ttl_seconds / 3600 / 24}天")
        except Exception as e:
            logger.warning(f"缓存处理后视频到Redis失败. key={key}, 错误: {e}")
