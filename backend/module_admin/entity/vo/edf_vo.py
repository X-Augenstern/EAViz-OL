from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import Optional, List
from datetime import datetime
from module_admin.annotation.pydantic_annotation import as_query


class EdfModel(BaseModel):
    """
    Edf表对应Pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    edf_id: Optional[int] = None
    edf_name: Optional[str] = None
    edf_sfreq: Optional[float] = None
    edf_time: Optional[float] = None
    edf_path: Optional[str] = None
    valid_channels: Optional[str] = None
    upload_by: Optional[str] = None
    upload_time: Optional[datetime] = None
    remark: Optional[str] = None


class EdfQueryModel(EdfModel):
    """
    Edf管理不分页查询模型
    """
    begin_time: Optional[str] = None
    end_time: Optional[str] = None


@as_query
class EdfPageQueryModel(EdfQueryModel):
    """
    Edf管理分页查询模型
    """
    page_num: int = 1
    page_size: int = 10


class AddEdfModel(EdfModel):
    """
    新增Edf模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    edf_list: List[EdfModel]
    user_id: int  # 必须提供


class DeleteEdfModel(BaseModel):
    """
    删除Edf模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    edf_ids: str


class EdfUserModel(BaseModel):
    """
    Edf和用户关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    edf_id: Optional[int] = None
    user_id: Optional[int] = None


class EdfUserQueryModel(EdfModel):
    """
    Edf用户关联管理不分页查询模型
    """
    user_id: Optional[int] = None


@as_query
class EdfUserPageQueryModel(EdfUserQueryModel):
    """
    Edf用户关联管理分页查询模型
    """
    page_num: int = 1
    page_size: int = 10


@as_query
class EdfDataQueryModel(BaseModel):
    """
    Edf数据查询模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    edf_id: int
    selected_channels: Optional[str] = None
    start: int = None
    end: int = None
