from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_camel
from typing import Union, Optional, List
from datetime import datetime
from module_admin.entity.vo.role_vo import RoleModel
from module_admin.entity.vo.dept_vo import DeptModel
from module_admin.entity.vo.post_vo import PostModel
from module_admin.annotation.pydantic_annotation import as_query, as_form


class TokenData(BaseModel):
    """
    token解析结果
    """
    user_id: Union[int, None] = None


class UserModel(BaseModel):
    """
    用户表对应pydantic模型（数据校验模型）
    """
    # Pydantic 提供了一种方式，通过 Config 类来定义字段的别名，允许在实例化模型时使用不同的字段名
    # 使用 alias_generator 来自动生成字段别名后，可以在实例化模型时使用别名字段名
    # from_attributes 设置为 True 后，Pydantic 模型可以从对象的属性中提取数据。这在需要从复杂对象（而不是简单的字典）中创建模型实例时特别有用
    # 通过这种配置，可以在 Pydantic 模型中使用驼峰命名法进行实例化，同时保持下划线命名法的字段定义。这使得代码更符合常见的命名规范，同时保持了模型的灵活性
    # print(user.user_id)  # 使用下划线命名来访问字段
    # print(user.dict(by_alias=True))  # 输出使用别名的字典
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)  # 模型配置，从属性名自动生成别名并转为驼峰

    user_id: Optional[int] = None
    dept_id: Optional[int] = None
    user_name: Optional[str] = None
    nick_name: Optional[str] = None
    user_type: Optional[str] = None
    email: Optional[str] = None
    phonenumber: Optional[str] = None
    sex: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    del_flag: Optional[str] = None
    login_ip: Optional[str] = None
    login_date: Optional[datetime] = None
    create_by: Optional[str] = None
    create_time: Optional[datetime] = None
    update_by: Optional[str] = None
    update_time: Optional[datetime] = None
    remark: Optional[str] = None
    admin: Optional[bool] = False  # add

    @model_validator(mode='after')  # 数据模型验证后执行
    def check_admin(self) -> 'UserModel':
        if self.user_id == 1:
            self.admin = True
        else:
            self.admin = False
        return self


class UserRoleModel(BaseModel):
    """
    用户和角色关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: Optional[int] = None
    role_id: Optional[int] = None


class UserPostModel(BaseModel):
    """
    用户与岗位关联表对应pydantic模型
    """
    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    user_id: Optional[int] = None
    post_id: Optional[int] = None


class UserInfoModel(UserModel):
    """
    获取用户信息响应模型
    """
    post_ids: Optional[str] = None
    role_ids: Optional[str] = None
    dept: Optional[DeptModel] = None
    role: Optional[List[Union[RoleModel, None]]] = []


class CurrentUserModel(BaseModel):
    """
    获取当前用户响应模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    permissions: List
    roles: List
    user: Union[UserInfoModel, None]


class UserDetailModel(BaseModel):
    """
    获取用户详情信息响应模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    data: Optional[UserInfoModel] = None
    post_ids: Optional[List] = None
    posts: List[Optional[PostModel]]
    role_ids: Optional[List] = None
    roles: List[Optional[RoleModel]]


class UserProfileModel(BaseModel):
    """
    获取个人信息响应模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    data: Optional[UserInfoModel]
    post_group: Union[str, None]
    role_group: Union[str, None]


class UserQueryModel(UserModel):
    """
    用户管理不分页查询模型
    """
    begin_time: Optional[str] = None
    end_time: Optional[str] = None


@as_query
@as_form  # 装饰器从下到上执行
class UserPageQueryModel(UserQueryModel):
    """
    用户管理分页查询模型

    通过装饰器依次将 as_form、as_query 方法添加到 UserPageQueryModel 类中

    这样，UserPageQueryModel 类既可以处理 GET 请求中的查询参数，又可以处理 POST 请求中的表单数据，非常方便
    """
    page_num: int = 1
    page_size: int = 10


class AddUserModel(UserModel):
    """
    新增用户模型
    """
    role_ids: Optional[List] = []
    post_ids: Optional[List] = []
    type: Optional[str] = None


class EditUserModel(AddUserModel):
    """
    编辑用户模型
    """
    role: Optional[List] = []


class ResetUserModel(UserModel):
    """
    重置用户密码模型
    """
    old_password: Optional[str] = None
    sms_code: Optional[str] = None
    session_id: Optional[str] = None


class DeleteUserModel(BaseModel):
    """
    删除用户模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    user_ids: str
    update_by: Optional[str] = None
    update_time: Optional[datetime] = None


class UserRoleQueryModel(UserModel):
    """
    用户角色关联管理不分页查询模型
    """
    role_id: Optional[int] = None


@as_query
class UserRolePageQueryModel(UserRoleQueryModel):
    """
    用户角色关联管理分页查询模型
    """
    page_num: int = 1
    page_size: int = 10


class SelectedRoleModel(RoleModel):
    """
    是否选择角色模型
    """
    flag: Optional[bool] = False


class UserRoleResponseModel(BaseModel):
    """
    用户角色关联管理列表返回模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    roles: List[Union[SelectedRoleModel, None]] = []
    user: UserInfoModel


@as_query
class CrudUserRoleModel(BaseModel):
    """
    新增、删除用户关联角色及角色关联用户模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    user_id: Optional[int] = None
    user_ids: Optional[str] = None  # 一/多个
    role_id: Optional[int] = None
    role_ids: Optional[str] = None  # 一/多个
