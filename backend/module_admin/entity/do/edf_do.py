from sqlalchemy import Column, Integer, String, DateTime, FLOAT
from config.database import Base
from datetime import datetime


class SysEdf(Base):
    """
    Edf表
    """
    __tablename__ = 'sys_edf'

    edf_id = Column(Integer, primary_key=True, autoincrement=True, comment='EDF文件ID')
    edf_name = Column(String(255), default='', comment='EDF文件名')
    edf_sfreq = Column(FLOAT, default='', comment='EDF采样频率')
    edf_time = Column(FLOAT, default='', comment='EDF采样时间')
    edf_path = Column(String(255), default='', comment='EDF文件路径')
    valid_channels = Column(String(255), default='', comment='有效通道')
    upload_by = Column(String(64), default='', comment='上传者')
    upload_time = Column(DateTime, default=datetime.now(), comment='上传时间')
    remark = Column(String(500), nullable=True, default='', comment='备注')


class SysEdfUser(Base):
    """
    Edf和用户关联表
    """
    __tablename__ = 'sys_edf_user'

    edf_id = Column(Integer, primary_key=True, nullable=False, comment='EDF文件ID')
    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
