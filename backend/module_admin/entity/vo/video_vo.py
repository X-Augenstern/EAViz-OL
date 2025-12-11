from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List

from module_admin.annotation.pydantic_annotation import as_query


class VideoModel(BaseModel):
    """
    视频表对应Pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    video_id: Optional[int] = None
    video_name: Optional[str] = None
    video_size: Optional[float] = None
    video_time: Optional[float] = None
    video_path: Optional[str] = None
    video_res: Optional[str] = None
    upload_by: Optional[str] = None
    upload_time: Optional[datetime] = None
    remark: Optional[str] = None


class VideoQueryModel(VideoModel):
    """
    视频管理不分页查询模型
    """
    begin_time: Optional[str] = None
    end_time: Optional[str] = None
    result_status: Optional[str] = None  # 分析结果状态：'seizure'（发作）或 'normal'（正常）


@as_query
class VideoPageQueryModel(VideoQueryModel):
    """
    视频管理分页查询模型
    """
    page_num: int = 1
    page_size: int = 10


class AddVideoModel(VideoModel):
    """
    新增视频模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    video_list: List[VideoModel]
    user_id: int  # 必须提供


class DeleteVideoModel(BaseModel):
    """
    删除视频模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    video_ids: str


class VideoUserModel(BaseModel):
    """
    视频和用户关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    video_id: Optional[int] = None
    user_id: Optional[int] = None


class VideoUserQueryModel(VideoModel):
    """
    视频用户关联管理不分页查询模型
    """
    user_id: Optional[int] = None


@as_query
class VideoUserPageQueryModel(VideoUserQueryModel):
    """
    视频用户关联管理分页查询模型
    """
    page_num: int = 1
    page_size: int = 10
