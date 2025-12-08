from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float

from config.database import Base


class SysVideo(Base):
    """
    视频表
    """
    __tablename__ = 'sys_video'

    video_id = Column(Integer, primary_key=True, autoincrement=True, comment='视频文件ID')
    video_name = Column(String(255), default='', comment='视频文件名')
    video_size = Column(Float, default=0.0, comment='视频文件大小')
    video_time = Column(Float, default=0.0, comment='视频文件时长')
    video_path = Column(String(255), default='', comment='视频文件路径')
    video_res = Column(String(255), default='', comment='视频文件分析结果')
    upload_by = Column(String(64), default='', comment='上传者')
    upload_time = Column(DateTime, default=datetime.now(), comment='上传时间')
    remark = Column(String(500), nullable=True, default='', comment='备注')


class SysVideoUser(Base):
    """
    视频和用户关联表
    """
    __tablename__ = 'sys_video_user'

    video_id = Column(Integer, primary_key=True, nullable=False, comment='视频文件ID')
    user_id = Column(Integer, primary_key=True, nullable=False, comment='用户ID')
