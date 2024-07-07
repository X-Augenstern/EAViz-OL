from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base
from datetime import datetime


class SysEdf(Base):
    """
    Edf表
    """
    __tablename__ = 'sys_edf'

    edf_id = Column(Integer, primary_key=True, autoincrement=True, comment='EDF文件ID')
    edf_name = Column(String(255), default='', comment='EDF文件名')
    edf_path = Column(String(255), default='', comment='EDF文件路径')
    upload_by = Column(String(64), default='', comment='上传者')
    upload_time = Column(DateTime, default=datetime.now(), comment='上传时间')
    remark = Column(String(500), nullable=True, default='', comment='备注')


class SysEdfUser(Base):
    """
    Edf和用户关联表
    """
    __tablename__ = 'sys_user_edf'

    edf_id = Column(Integer, primary_key=True, nullable=False, comment='EDF文件ID')
    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
