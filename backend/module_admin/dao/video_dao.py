from datetime import time
from sqlalchemy import and_
from sqlalchemy.orm import Session

from module_admin.entity.do.video_do import *
from module_admin.entity.vo.video_vo import *
from utils.page_util import PageUtil


class VideoDao:
    """
    视频管理模块数据库操作层
    """

    @classmethod
    def get_video_by_id(cls, db: Session, video_id: int):
        """
        根据video的id获取video信息
        """
        video_info = db.query(SysVideo).filter(and_(SysVideo.video_id == video_id)).first()
        return video_info

    @classmethod
    def get_video_list(cls, db: Session, user_id: int, query_object: VideoPageQueryModel, is_page: bool = False):
        """
        根据查询参数（video名字、上传者、上传时间）获取video列表信息
        """
        conditions = []

        if user_id != 1:
            conditions.append(SysVideoUser.user_id == user_id)
        if query_object.video_name:
            conditions.append(SysVideo.video_name.like(f'%{query_object.video_name}%'))
        if query_object.upload_by:
            conditions.append(SysVideo.upload_by.like(f'%{query_object.upload_by}%'))
        if query_object.begin_time and query_object.end_time:
            conditions.append(SysVideo.upload_time.between(
                datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'),
                                 time(00, 00, 00)),
                datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'),
                                 time(23, 59, 59))))

        query = (db.query(SysVideo)
                 .join(SysVideoUser, and_(SysVideo.video_id == SysVideoUser.video_id))
                 .filter(and_(*conditions))
                 .order_by(SysVideo.video_id.desc())
                 .distinct())
        video_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return video_list

    @classmethod
    def add_video_dao(cls, db: Session, video: VideoModel):
        """
        新增Video数据库操作
        """
        # 检查是否已经存在具有相同 video_name 和 video_path 的 video
        existing_video = db.query(SysVideo).filter(
            and_(SysVideo.video_name == video.video_name, SysVideo.video_path == video.video_path)).first()
        if existing_video:
            return None

        db_video = SysVideo(**video.model_dump())
        db.add(db_video)
        db.flush()

        return db_video

    @classmethod
    def delete_video_dao(cls, db: Session, video: VideoModel):
        """
        删除Video数据库操作
        """
        db.query(SysVideo).filter(and_(SysVideo.video_id == video.video_id)).delete()

    @classmethod
    def add_video_user_dao(cls, db: Session, user_video: VideoUserModel):
        """
        新增Video用户关联信息数据库操作
        """
        db_user_video = SysVideoUser(**user_video.model_dump())
        db.add(db_user_video)

    @classmethod
    def delete_video_user_dao(cls, db: Session, user_video: VideoUserModel):
        """
        删除Video用户关联信息数据库操作
        """
        db.query(SysVideoUser).filter(and_(SysVideoUser.video_id == user_video.video_id)).delete()

    @classmethod
    def get_video_user_dao(cls, db: Session, user_video: VideoUserModel):
        """
        根据用户id和video的id获取用户Video关联详细信息
        """
        user_video_info = db.query(SysVideoUser).filter(and_(SysVideoUser.user_id == user_video.user_id,
                                                             SysVideoUser.video_id == user_video.video_id)).distinct().first()

        return user_video_info

    @classmethod
    def get_video_list_by_user_id(cls, db: Session, query_object: VideoUserPageQueryModel, is_page: bool = False):
        """
        根据用户id获取用户拥有的Video列表信息
        """
        query = (db.query(SysVideo, SysVideoUser.user_id)
                 .join(SysVideoUser,
                       and_(SysVideo.video_id == SysVideoUser.video_id,
                            SysVideoUser.user_id == query_object.user_id)).distinct())

        video_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)
        return video_list
