from sqlalchemy.orm import Session
from sqlalchemy import and_
from module_admin.entity.do.edf_do import *
from module_admin.entity.vo.edf_vo import *
from utils.page_util import PageUtil
from datetime import datetime, time


class EdfDao:
    """
    Edf管理模块数据库操作层
    """

    @classmethod
    def get_edf_by_id(cls, db: Session, edf_id: int):
        """
        根据edf的id获取edf信息
        """
        edf_info = db.query(SysEdf).filter(and_(SysEdf.edf_id == edf_id)).first()
        return edf_info

    @classmethod
    def get_edf_list(cls, db: Session, query_object: EdfPageQueryModel, is_page: bool = False):
        """
        根据查询参数（edf名字、上传者、上传时间）获取edf列表信息
        """
        conditions = []
        if query_object.edf_name:
            conditions.append(SysEdf.edf_name.like(f'%{query_object.edf_name}%'))
        if query_object.upload_by:
            conditions.append(SysEdf.upload_by.like(f'%{query_object.upload_by}%'))
        if query_object.begin_time and query_object.end_time:
            conditions.append(SysEdf.upload_time.between(
                datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'),
                                 time(00, 00, 00)),
                datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'),
                                 time(23, 59, 59))))

        query = db.query(SysEdf).filter(and_(*conditions)).order_by(SysEdf.edf_id).distinct()

        edf_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return edf_list

    @classmethod
    def add_edf_dao(cls, db: Session, edf: EdfModel):
        """
        新增Edf数据库操作
        """
        # 检查是否已经存在具有相同 edf_name 和 edf_path 的 edf
        existing_edf = db.query(SysEdf).filter(
            and_(SysEdf.edf_name == edf.edf_name, SysEdf.edf_path == edf.edf_path)).first()
        if existing_edf:
            return None

        db_edf = SysEdf(**edf.model_dump())
        db.add(db_edf)
        db.flush()

        return db_edf

    @classmethod
    def delete_edf_dao(cls, db: Session, edf: EdfModel):
        """
        删除Edf数据库操作
        """
        db.query(SysEdf).filter(and_(SysEdf.edf_id == edf.edf_id)).delete()

    @classmethod
    def add_edf_user_dao(cls, db: Session, user_edf: EdfUserModel):
        """
        新增Edf用户关联信息数据库操作
        """
        db_user_edf = SysEdfUser(**user_edf.model_dump())
        db.add(db_user_edf)

    @classmethod
    def delete_edf_user_dao(cls, db: Session, user_edf: EdfUserModel):
        """
        删除Edf用户关联信息数据库操作
        """
        db.query(SysEdfUser).filter(and_(SysEdfUser.edf_id == user_edf.edf_id)).delete()

    @classmethod
    def get_edf_user_dao(cls, db: Session, user_edf: EdfUserModel):
        """
        根据用户id和edf的id获取用户Edf关联详细信息
        """
        user_edf_info = db.query(SysEdfUser).filter(and_(SysEdfUser.user_id == user_edf.user_id,
                                                         SysEdfUser.edf_id == user_edf.edf_id)).distinct().first()

        return user_edf_info

    @classmethod
    def get_edf_list_by_user_id(cls, db: Session, query_object: EdfUserPageQueryModel, is_page: bool = False):
        """
        根据用户id获取用户拥有的Edf列表信息
        """
        query = (db.query(SysEdf, SysEdfUser.user_id)
                 .join(SysEdfUser,
                       and_(SysEdf.edf_id == SysEdfUser.edf_id, SysEdfUser.user_id == query_object.user_id)).distinct())

        edf_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return edf_list
