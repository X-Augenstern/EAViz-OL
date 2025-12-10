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

        # SQLAlchemy 中 Session.add() 仅将对象加入会话（标记为「pending」状态），但不会立即和数据库交互；而 Session.flush() 会：
        # 把会话中待执行的 INSERT/UPDATE/DELETE 语句发送到数据库执行（但不提交事务）；
        # 若表的主键（video_id）是数据库自增类型（如 MySQL 的 AUTO_INCREMENT、PostgreSQL 的 SERIAL），数据库执行 INSERT 后会生成主键值，SQLAlchemy 会自动将这个值回填到 db_video 对象的 video_id 属性
        # 简单说：add() 是「标记要插入」，flush() 是「真正执行插入并拿回主键」。

        # 如果 video_id 是手动赋值（如 UUID、业务自定义 ID），则 flush() 不会回填（因为插入前就已有值）；如果是数据库生成的自增 ID，flush() 后必然会回填。

        # flush() 不等于 commit()：flush() 仅执行 SQL 但未提交事务，若后续调用 db.rollback()，数据库中不会保留这条记录，但 db_video 上的 video_id 仍会存在（只是数据库侧已回滚）；
        # 若 flush() 失败（如约束冲突、数据库异常），会抛出异常，此时 video_id 不会被回填；
        # 若仅调用 db.add(db_video) 而不 flush()/commit()，video_id 仍为 None（因为未和数据库交互）。
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
