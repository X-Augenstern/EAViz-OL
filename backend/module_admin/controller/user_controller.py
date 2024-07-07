from fastapi import APIRouter, Request
from fastapi import Depends, File, Query
from config.get_db import get_db
from config.env import UploadConfig
from module_admin.service.login_service import LoginService
from module_admin.service.user_service import *
from module_admin.service.dept_service import DeptService
from utils.page_util import PageResponseModel
from utils.response_util import *
from utils.log_util import *
from utils.common_util import bytes2file_response
from utils.upload_util import UploadUtil
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.aspect.data_scope import GetDataScope
from module_admin.annotation.log_annotation import log_decorator
from os import path, makedirs

userController = APIRouter(prefix='/system/user', dependencies=[Depends(LoginService.get_current_user)])


# 当访问/system/user/deptTree节点时，FastAPI会按以下顺序处理请求：
# 1、全局依赖项处理 —— 获取当前用户：
# userController的APIRouter定义了一个全局依赖项dependencies=[Depends(LoginService.get_current_user)]
# 因此，在访问任何以/system/user为前缀的路由时，都会先调用LoginService.get_current_user来获取当前用户
# 2、路由依赖项处理 —— 权限校验：
# 对于具体的路由/deptTree，还定义了一个依赖项dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))]
# 因此，FastAPI会实例化CheckUserInterfaceAuth并调用其实例的__call__方法来校验当前用户是否具有system:user:list权限
# 如果检验失败，抛出权限异常，返回相应的HTTP错误响应
# 3、路由处理函数依赖项处理 —— 获取数据库会话、获取sql查询条件：
# 如果在路由处理函数的依赖项中出现异常，那么这个路由处理函数将不会执行，会立即停止处理并返回一个适当的HTTP响应，这个响应通常是由引发的异常决定的
# 4、路由处理函数：
# 如果所有依赖项都成功执行且未抛出异常，FastAPI会调用实际的路由处理函数get_system_dept_tree
@userController.get("/deptTree", dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))])
async def get_system_dept_tree(request: Request, query_db: Session = Depends(get_db),
                               data_scope_sql: str = Depends(GetDataScope('SysDept'))):
    """
    使用当前用户的dept_id获取部门树
    """
    try:
        # DeptModel(**{}) 相当于调用 DeptModel()
        dept_query_result = DeptService.get_dept_tree_services(query_db, DeptModel(**{}), data_scope_sql)
        logger.info('获取成功')
        return ResponseUtil.success(data=dept_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


# 以下是 FastAPI 在处理 response_model 验证时的具体步骤：
# 1、执行路由函数：
# FastAPI 首先执行 get_system_user_list 路由函数。
# 2、调用 ResponseUtil.success 函数：
# 在路由函数内部，调用 ResponseUtil.success，它会将 user_page_query_result 转换为字典，并创建一个 JSONResponse 对象。
# 3、FastAPI 校验和转换：
# FastAPI 对返回的 JSONResponse 对象进行校验，确保其内容符合 PageResponseModel 的结构要求。
# 即使响应中包含额外的字段，只要 PageResponseModel 所有必需字段都存在并符合类型要求，校验就能通过。
# 4、返回响应：
# 如果校验通过，FastAPI 将响应数据返回给客户端；如果不符合 PageResponseModel 的结构，FastAPI 将返回 422 错误响应。

# 1、请求解析：
# FastAPI 在接收到 HTTP 请求时，首先解析请求的 URL、Headers、Body 等部分。对于从 URL 查询字符串中获取参数的情况，FastAPI 会解析 URL 中的 ?key=value 格式的参数。
# 2、参数匹配与传递：
# FastAPI 会查看 as_query 方法定义的参数。如果 as_query 方法定义了接收特定参数的能力（比如定义了接收 page_num 和 page_size 的参数），会尝试从请求的查询字符串中提取这些参数。
# FastAPI 使用 Pydantic 模型来进行数据验证和序列化。
# 所以，如果 as_query 方法是作为一个 Pydantic 模型的工厂方法实现的，FastAPI 将会实例化这个模型，并自动将解析的查询参数作为构造函数的参数传递进去。
# 3、依赖注入执行：
# 一旦 as_query 方法接收到了所需的参数，它会进行任何必要的处理（如参数验证、数据转换等），然后返回一个相应的实例或数据。
# 这个返回值随后被用作相应的依赖项在接下来的请求处理过程中（如路由处理函数中）。
@userController.get("/list", response_model=PageResponseModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:user:list'))])
async def get_system_user_list(request: Request,
                               user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query),
                               query_db: Session = Depends(get_db),
                               data_scope_sql: str = Depends(GetDataScope('SysUser'))):
    """
    获取用户列表分页数据

    从提供的函数参数列表可以看出，URL的查询参数会包含UserPageQueryModel中定义的所有字段。这是因为在FastAPI中，使用Depends和Pydantic模型的方式可以自动将查询参数解析并绑定到模型中。

    所以，使用as_query可以把一个类里面的全部字段转化为Query参数，以便FastAPI自动将请求URL中的查询参数解析并绑定到UserPageQueryModel实例user_page_query中。

    这样就可以直接在函数中使用这个实例来访问查询参数。
    """
    try:
        user_page_query_result = UserService.get_user_list_services(query_db, user_page_query, data_scope_sql,
                                                                    is_page=True)
        logger.info('获取成功')
        return ResponseUtil.success(model_content=user_page_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.post("", dependencies=[Depends(CheckUserInterfaceAuth('system:user:add'))])
@log_decorator(title='用户管理', business_type=1)
async def add_system_user(request: Request, add_user: AddUserModel, query_db: Session = Depends(get_db),
                          current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    新增用户
    """
    try:
        add_user.password = PwdUtil.get_password_hash(add_user.password)
        add_user.create_by = current_user.user.user_name
        add_user.update_by = current_user.user.user_name
        add_user_result = UserService.add_user_services(query_db, add_user)
        if add_user_result.is_success:
            logger.info(add_user_result.message)
            return ResponseUtil.success(msg=add_user_result.message)
        else:
            logger.warning(add_user_result.message)
            return ResponseUtil.failure(msg=add_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("", dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@log_decorator(title='用户管理', business_type=2)
async def edit_system_user(request: Request, edit_user: EditUserModel, query_db: Session = Depends(get_db),
                           current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    编辑用户
    """
    try:
        edit_user.update_by = current_user.user.user_name
        edit_user.update_time = datetime.now()
        edit_user_result = UserService.edit_user_services(query_db, edit_user)
        if edit_user_result.is_success:
            logger.info(edit_user_result.message)
            return ResponseUtil.success(msg=edit_user_result.message)
        else:
            logger.warning(edit_user_result.message)
            return ResponseUtil.failure(msg=edit_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.delete("/{user_ids}", dependencies=[Depends(CheckUserInterfaceAuth('system:user:remove'))])
@log_decorator(title='用户管理', business_type=3)
async def delete_system_user(request: Request, user_ids: str, query_db: Session = Depends(get_db),
                             current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    删除用户
    """
    try:
        delete_user = DeleteUserModel(
            userIds=user_ids,
            updateBy=current_user.user.user_name,
            updateTime=datetime.now()
        )
        delete_user_result = UserService.delete_user_services(query_db, delete_user)
        if delete_user_result.is_success:
            logger.info(delete_user_result.message)
            return ResponseUtil.success(msg=delete_user_result.message)
        else:
            logger.warning(delete_user_result.message)
            return ResponseUtil.failure(msg=delete_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("/resetPwd", dependencies=[Depends(CheckUserInterfaceAuth('system:user:resetPwd'))])
@log_decorator(title='用户管理', business_type=2)
async def reset_system_user_pwd(request: Request, edit_user: EditUserModel, query_db: Session = Depends(get_db),
                                current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    修改用户密码
    """
    try:
        edit_user.password = PwdUtil.get_password_hash(edit_user.password)
        edit_user.update_by = current_user.user.user_name
        edit_user.update_time = datetime.now()
        edit_user.type = 'pwd'
        edit_user_result = UserService.edit_user_services(query_db, edit_user)
        if edit_user_result.is_success:
            logger.info(edit_user_result.message)
            return ResponseUtil.success(msg=edit_user_result.message)
        else:
            logger.warning(edit_user_result.message)
            return ResponseUtil.failure(msg=edit_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("/changeStatus", dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
@log_decorator(title='用户管理', business_type=2)
async def change_system_user_status(request: Request, edit_user: EditUserModel, query_db: Session = Depends(get_db),
                                    current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    改变用户状态
    """
    try:
        edit_user.update_by = current_user.user.user_name
        edit_user.update_time = datetime.now()
        edit_user.type = 'status'
        edit_user_result = UserService.edit_user_services(query_db, edit_user)
        if edit_user_result.is_success:
            logger.info(edit_user_result.message)
            return ResponseUtil.success(msg=edit_user_result.message)
        else:
            logger.warning(edit_user_result.message)
            return ResponseUtil.failure(msg=edit_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.get("/profile", response_model=UserProfileModel)
async def query_detail_system_user(request: Request, query_db: Session = Depends(get_db),
                                   current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取当前用户详细信息
    """
    try:
        profile_user_result = UserService.user_profile_services(query_db, current_user.user.user_id)
        logger.info(f'获取user_id为{current_user.user.user_id}的信息成功')
        return ResponseUtil.success(model_content=profile_user_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.get("/{user_id}", response_model=UserDetailModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))])
@userController.get("/", response_model=UserDetailModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))])
async def query_detail_system_user(request: Request, user_id: Optional[Union[int, str]] = '',
                                   query_db: Session = Depends(get_db)):
    """
    获取用户详细信息（有user_id），否则获取岗位、角色列表信息
    """
    try:
        detail_user_result = UserService.user_detail_services(query_db, user_id)
        logger.info(f'获取user_id为{user_id}的信息成功')
        return ResponseUtil.success(model_content=detail_user_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.post("/profile/avatar")
@log_decorator(title='个人信息', business_type=2)
async def change_system_user_profile_avatar(request: Request, avatarfile: bytes = File(),
                                            query_db: Session = Depends(get_db),
                                            current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    修改用户头像
    """
    try:
        relative_path = f'avatar/{datetime.now().strftime("%Y")}/{datetime.now().strftime("%m")}/{datetime.now().strftime("%d")}'
        dir_path = path.join(UploadConfig.UPLOAD_PATH, relative_path)
        try:
            makedirs(dir_path)
        except FileExistsError:
            pass
        avatar_name = f'avatar_{datetime.now().strftime("%Y%m%d%H%M%S")}{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.png'
        # 用户上传的头像将被存储于服务器路径：files/upload_path/avatar/2024/05/29/avatar_20240529123045A001.png
        avatar_path = path.join(dir_path, avatar_name)
        with open(avatar_path, 'wb') as f:
            f.write(avatarfile)
        edit_user = EditUserModel(
            userId=current_user.user.user_id,
            # /profile/avatar/2024/07/07/avatar_20240707150538A004.png
            # 前端获取到后 -> /dev-api/profile/avatar/2024/07/07/avatar_20240707150538A004.png
            # 前端根据此url从后端获取资源 -> rewrite -> /profile/avatar/2024/07/07/avatar_20240707150538A004.png
            # 代理发送至后端服务器 http://localhost:9099
            # 后端将/profile映射为files/upload_path -> files/upload_path/avatar/2024/07/07/avatar_20240707150538A004.png
            avatar=f'{UploadConfig.UPLOAD_PREFIX}/{relative_path}/{avatar_name}',
            updateBy=current_user.user.user_name,
            updateTime=datetime.now(),
            type='avatar'
        )
        edit_user_result = UserService.edit_user_services(query_db, edit_user)
        if edit_user_result.is_success:
            logger.info(edit_user_result.message)
            return ResponseUtil.success(dict_content={'imgUrl': edit_user.avatar}, msg=edit_user_result.message)
        else:
            logger.warning(edit_user_result.message)
            return ResponseUtil.failure(msg=edit_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("/profile")
@log_decorator(title='个人信息', business_type=2)
async def change_system_user_profile_info(request: Request, user_info: UserInfoModel,
                                          query_db: Session = Depends(get_db),
                                          current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    修改用户信息
    """
    try:
        edit_user = EditUserModel(**user_info.model_dump(by_alias=True, exclude={'role_ids', 'post_ids'}),
                                  roleIds=user_info.role_ids.split(','), postIds=user_info.post_ids.split(','))
        edit_user.user_id = current_user.user.user_id
        edit_user.update_by = current_user.user.user_name
        edit_user.update_time = datetime.now()
        # print(edit_user.model_dump())
        edit_user_result = UserService.edit_user_services(query_db, edit_user)
        if edit_user_result.is_success:
            logger.info(edit_user_result.message)
            return ResponseUtil.success(msg=edit_user_result.message)
        else:
            logger.warning(edit_user_result.message)
            return ResponseUtil.failure(msg=edit_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("/profile/updatePwd")
@log_decorator(title='个人信息', business_type=2)
async def reset_system_user_password(request: Request, old_password: str = Query(alias='oldPassword'),
                                     new_password: str = Query(alias='newPassword'),
                                     query_db: Session = Depends(get_db),
                                     current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    修改用户密码

    从提供的函数参数列表可以看出，URL中会包含查询参数old_password和new_password。
    e.g. PUT /system/user/profile/updatePwd?oldPassword=your_old_password&newPassword=your_new_password
    """
    try:
        reset_user = ResetUserModel(
            userId=current_user.user.user_id,
            oldPassword=old_password,
            password=PwdUtil.get_password_hash(new_password),
            updateBy=current_user.user.user_name,
            updateTime=datetime.now()
        )
        reset_user_result = UserService.reset_user_services(query_db, reset_user)
        if reset_user_result.is_success:
            logger.info(reset_user_result.message)
            return ResponseUtil.success(msg=reset_user_result.message)
        else:
            logger.warning(reset_user_result.message)
            return ResponseUtil.failure(msg=reset_user_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.post("/importData", dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
@log_decorator(title='用户管理', business_type=6)
async def batch_import_system_user(request: Request, file: UploadFile = File(...),
                                   update_support: bool = Query(alias='updateSupport'),
                                   query_db: Session = Depends(get_db),
                                   current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    批量导入用户
    """
    try:
        batch_import_result = await UserService.batch_import_user_services(query_db, file, update_support, current_user)
        if batch_import_result.is_success:
            logger.info(batch_import_result.message)
            return ResponseUtil.success(msg=batch_import_result.message)
        else:
            logger.warning(batch_import_result.message)
            return ResponseUtil.failure(msg=batch_import_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.post("/importTemplate", dependencies=[Depends(CheckUserInterfaceAuth('system:user:import'))])
async def export_system_user_template(request: Request, query_db: Session = Depends(get_db)):
    """
    获取导入用户模板
    """
    try:
        user_import_template_result = UserService.get_user_import_template_services()
        logger.info('获取成功')
        return ResponseUtil.streaming(data=bytes2file_response(user_import_template_result))
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.post("/export", dependencies=[Depends(CheckUserInterfaceAuth('system:user:export'))])
@log_decorator(title='用户管理', business_type=5)
async def export_system_user_list(request: Request,
                                  user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_form),
                                  query_db: Session = Depends(get_db),
                                  data_scope_sql: str = Depends(GetDataScope('SysUser'))):
    """
    导出用户
    """
    try:
        # 获取全量数据
        user_query_result = UserService.get_user_list_services(query_db, user_page_query, data_scope_sql, is_page=False)
        user_export_result = UserService.export_user_list_services(user_query_result)
        logger.info('导出成功')
        return ResponseUtil.streaming(data=bytes2file_response(user_export_result))
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.get("/authRole/{user_id}", response_model=UserRoleResponseModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:user:query'))])
async def get_system_allocated_role_list(request: Request, user_id: int, query_db: Session = Depends(get_db)):
    """
    根据用户获取已分配角色列表
    """
    try:
        user_role_query = UserRoleQueryModel(userId=user_id)
        user_role_allocated_query_result = UserService.get_user_role_allocated_list_services(query_db, user_role_query)
        logger.info('获取成功')
        return ResponseUtil.success(model_content=user_role_allocated_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@userController.put("/authRole", response_model=UserRoleResponseModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:user:edit'))])
async def update_system_role_user(request: Request, user_id: int = Query(alias='userId'),
                                  role_ids: str = Query(alias='roleIds'), query_db: Session = Depends(get_db)):
    """
    给用户添加角色
    """
    try:
        add_user_role_result = UserService.add_user_role_services(query_db,
                                                                  CrudUserRoleModel(userId=user_id, roleIds=role_ids))
        if add_user_role_result.is_success:
            logger.info(add_user_role_result.message)
            return ResponseUtil.success(msg=add_user_role_result.message)
        else:
            logger.warning(add_user_role_result.message)
            return ResponseUtil.failure(msg=add_user_role_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
