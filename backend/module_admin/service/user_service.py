from fastapi import UploadFile
from module_admin.service.role_service import RoleService
from module_admin.service.post_service import PostService, PostPageQueryModel
from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.dao.user_dao import *
from utils.page_util import PageResponseModel
from utils.pwd_util import *
from utils.common_util import *
from io import BytesIO
from pandas import read_excel


class UserService:
    """
    用户管理模块服务层
    """
    @classmethod
    def get_user_list_services(cls, query_db: Session, query_object: UserPageQueryModel, data_scope_sql: str,
                               is_page: bool = False):
        """
        获取用户列表信息service
        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        # is_page = True：return PageResponseModel
        # is_page = False：return CamelCaseUtil.transform_result(no_paginated_data)

        # 将数据库查询结果转换为具有统一格式的分页响应，包括用户数据和分页详情，其中用户数据还特别加上了部门信息
        # 这样的处理使得前端或调用者能够方便地处理和显示分页和用户数据
        query_result = UserDao.get_user_list(query_db, query_object, data_scope_sql, is_page)
        if is_page:
            user_list_result = PageResponseModel(
                # 将所有键值对合并生成新的字典再解构到 PageResponseModel 类完成实例化
                **{
                    # 将 query_result 的属性和值转换为字典形式再解构出来
                    **query_result.model_dump(by_alias=True),
                    # 将 rows 键的值修改为一个由用户信息和部门信息组成的字典列表
                    # query = db.query(SysUser, SysDept) 所以**row[0]：各项用户信息键值对、row[1]部门信息
                    'rows': [{**row[0], 'dept': row[1]} for row in query_result.rows]
                }
            )
        else:
            user_list_result = []
            if query_result:
                user_list_result = [{**row[0], 'dept': row[1]} for row in query_result]

        return user_list_result

    @classmethod
    def add_user_services(cls, query_db: Session, page_object: AddUserModel):
        """
        新增用户信息service
        :param query_db: orm对象
        :param page_object: 新增用户对象
        :return: 新增用户校验结果
        """
        add_user = UserModel(**page_object.model_dump(by_alias=True))
        user = UserDao.get_user_by_info(query_db, UserModel(userName=page_object.user_name))
        if user:
            result = dict(is_success=False, message='用户名已存在')
        else:
            try:
                add_result = UserDao.add_user_dao(query_db, add_user)
                user_id = add_result.user_id
                if page_object.role_ids:
                    for role in page_object.role_ids:
                        UserDao.add_user_role_dao(query_db, UserRoleModel(userId=user_id, roleId=role))
                if page_object.post_ids:
                    for post in page_object.post_ids:
                        UserDao.add_user_post_dao(query_db, UserPostModel(userId=user_id, postId=post))
                # flush() 方法会将当前会话中挂起的所有更改（如插入、更新、删除操作）立即推送到数据库中
                # 这意味着这些更改会被写入数据库，但不会提交事务。因此，如果会话在 flush() 之后失败或回滚，这些更改仍然可以被撤销
                # commit() 方法用于提交事务。提交事务后，所有挂起的更改都会永久写入数据库，不可撤销。即使发生系统故障，这些更改也不会丢失
                query_db.commit()
                result = dict(is_success=True, message='新增成功')
            except Exception as e:
                query_db.rollback()  # 出现异常，回滚事务
                raise e

        return CrudResponseModel(**result)

    @classmethod
    def edit_user_services(cls, query_db: Session, page_object: EditUserModel):
        """
        编辑用户信息service
        :param query_db: orm对象
        :param page_object: 编辑用户对象
        :return: 编辑用户校验结果
        """
        # exclude_unset：将显式赋值过的属性转换为字典格式。未设置的属性将不会包含在字典中。
        # exclude={'admin'}：从生成的字典中排除 admin 属性，即使它已被设置过。
        edit_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        if page_object.type != 'status' and page_object.type != 'avatar' and page_object.type != 'pwd':
            del edit_user['role_ids']
            del edit_user['post_ids']
            del edit_user['role']
        if page_object.type == 'status' or page_object.type == 'avatar' or page_object.type == 'pwd':
            del edit_user['type']
        user_info = cls.user_detail_services(query_db, edit_user.get('user_id'))
        if user_info:
            if page_object.type != 'status' and page_object.type != 'avatar' and page_object.type == 'pwd' and user_info.data.user_name != page_object.user_name:
                user = UserDao.get_user_by_info(query_db, UserModel(userName=page_object.user_name))
                if user:
                    result = dict(is_success=False, message='用户名已存在')
                    return CrudResponseModel(**result)
            try:
                UserDao.edit_user_dao(query_db, edit_user)
                if page_object.type != 'status' and page_object.type != 'avatar':
                    UserDao.delete_user_role_dao(query_db, UserRoleModel(userId=page_object.user_id))
                    UserDao.delete_user_post_dao(query_db, UserPostModel(userId=page_object.user_id))
                    if page_object.role_ids:
                        for role in page_object.role_ids:
                            UserDao.add_user_role_dao(query_db, UserRoleModel(userId=page_object.user_id, roleId=role))
                    if page_object.post_ids:
                        for post in page_object.post_ids:
                            UserDao.add_user_post_dao(query_db, UserPostModel(userId=page_object.user_id, postId=post))
                query_db.commit()
                result = dict(is_success=True, message='更新成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='用户不存在')

        return CrudResponseModel(**result)

    @classmethod
    def delete_user_services(cls, query_db: Session, page_object: DeleteUserModel):
        """
        删除用户信息service
        :param query_db: orm对象
        :param page_object: 删除用户对象
        :return: 删除用户校验结果
        """
        if page_object.user_ids:  # 删除一/多个
            user_id_list = page_object.user_ids.split(',')
            try:
                for user_id in user_id_list:
                    user_id_dict = dict(userId=user_id, updateBy=page_object.update_by,
                                        updateTime=page_object.update_time)
                    UserDao.delete_user_role_dao(query_db, UserRoleModel(**user_id_dict))
                    UserDao.delete_user_post_dao(query_db, UserPostModel(**user_id_dict))
                    UserDao.delete_user_dao(query_db, UserModel(**user_id_dict))
                query_db.commit()
                result = dict(is_success=True, message='删除成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='传入用户id为空')
        return CrudResponseModel(**result)

    @classmethod
    def user_detail_services(cls, query_db: Session, user_id: Union[int, str]):
        """
        获取用户详细信息service
        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        # PostPageQueryModel(**{}) 创建一个 PostPageQueryModel 类的实例，并使用默认值初始化所有字段。等同于直接调用 PostPageQueryModel()
        posts = PostService.get_post_list_services(query_db, PostPageQueryModel(**{}), is_page=False)
        roles = RoleService.get_role_select_option_services(query_db)
        if user_id != '':
            query_user = UserDao.get_user_detail_by_id(query_db, user_id=user_id)
            post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
            post_ids_list = [row.post_id for row in query_user.get('user_post_info')]
            role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
            role_ids_list = [row.role_id for row in query_user.get('user_role_info')]

            return UserDetailModel(
                data=UserInfoModel(
                    **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                    postIds=post_ids,
                    roleIds=role_ids,
                    dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                    role=CamelCaseUtil.transform_result(query_user.get('user_role_info'))
                ),
                postIds=post_ids_list,
                posts=posts,
                roleIds=role_ids_list,
                roles=roles
            )

        return UserDetailModel(
            posts=posts,
            roles=roles
        )

    @classmethod
    def user_profile_services(cls, query_db: Session, user_id: int):
        """
        获取用户详细信息service
        :param query_db: orm对象
        :param user_id: 用户id
        :return: 用户id对应的信息
        """
        query_user = UserDao.get_user_detail_by_id(query_db, user_id=user_id)
        post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
        post_group = ','.join([row.post_name for row in query_user.get('user_post_info')])
        role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
        role_group = ','.join([row.role_name for row in query_user.get('user_role_info')])

        return UserProfileModel(
            data=UserInfoModel(
                **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
                postIds=post_ids,
                roleIds=role_ids,
                dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
                role=CamelCaseUtil.transform_result(query_user.get('user_role_info'))
            ),
            postGroup=post_group,
            roleGroup=role_group
        )

    @classmethod
    def reset_user_services(cls, query_db: Session, page_object: ResetUserModel):
        """
        重置用户密码service
        :param query_db: orm对象
        :param page_object: 重置用户对象
        :return: 重置用户校验结果
        """
        reset_user = page_object.model_dump(exclude_unset=True, exclude={'admin'})
        if page_object.old_password:
            user = UserDao.get_user_detail_by_id(query_db, user_id=page_object.user_id).get('user_basic_info')
            if not PwdUtil.verify_password(page_object.old_password, user.password):
                result = dict(is_success=False, message='旧密码不正确')
                return CrudResponseModel(**result)
            else:
                del reset_user['old_password']
        if page_object.sms_code and page_object.session_id:
            del reset_user['sms_code']
            del reset_user['session_id']
        try:
            UserDao.edit_user_dao(query_db, reset_user)
            query_db.commit()
            result = dict(is_success=True, message='重置成功')
        except Exception as e:
            query_db.rollback()
            raise e

        return CrudResponseModel(**result)

    @classmethod
    async def batch_import_user_services(cls, query_db: Session, file: UploadFile, update_support: bool,
                                         current_user: CurrentUserModel):
        """
        批量导入用户service
        :param query_db: orm对象
        :param file: 用户导入文件对象
        :param update_support: 用户存在时是否更新
        :param current_user: 当前用户对象
        :return: 批量导入用户结果
        """
        # 并非所有耗时任务都必须使用异步函数，但使用异步函数可以提高应用的性能，特别是在处理I/O密集型任务（如数据库操作、文件读写、网络请求等）时
        # 1、对于I/O密集型的操作，如数据库访问、网络调用或文件系统操作，使用异步代码可以显著提高性能。这是因为这些操作通常涉及等待外部系统完成工作，
        # 而CPU在这段时间内几乎不进行任何处理。通过使用异步操作，当任务处于等待状态时，FastAPI 可以自由地处理其他请求，而不是闲置等待
        # 2、对于CPU密集型任务，如复杂计算或大规模数据处理，异步函数并不会带来性能上的优势。这类任务主要受到CPU处理能力的限制，而非I/O等待
        # 在这种情况下，使用多线程或多进程可能是更好的解决方案。对于这些操作，可以考虑使用如 concurrent.futures 库中的 ThreadPoolExecutor 或 ProcessPoolExecutor

        # 将Excel表头中的中文列名映射到数据库对应的英文字段名
        header_dict = {
            "部门编号": "dept_id",
            "登录名称": "user_name",
            "用户名称": "nick_name",
            "用户邮箱": "email",
            "手机号码": "phonenumber",
            "用户性别": "sex",
            "帐号状态": "status"
        }
        # await用于等待异步操作完成，并且这种用法能够防止程序在文件读取过程中阻塞，使得其他并行操作能够继续执行
        contents = await file.read()  # 从上传的文件中获取二进制数据
        df = read_excel(BytesIO(contents))  # 创建了一个类似于文件的对象，这使得 contents 可以被像文件一样处理，解析其内容并将数据加载到DataFrame中
        await file.close()
        df.rename(columns=header_dict, inplace=True)  # 将列名通过rename方法替换为英文字段名
        add_error_result = []
        count = 0
        try:
            for index, row in df.iterrows():
                count = count + 1
                if row['sex'] == '男':
                    row['sex'] = '0'
                if row['sex'] == '女':
                    row['sex'] = '1'
                if row['sex'] == '未知':
                    row['sex'] = '2'
                if row['status'] == '正常':
                    row['status'] = '0'
                if row['status'] == '停用':
                    row['status'] = '1'
                add_user = UserModel(
                    deptId=row['dept_id'],
                    userName=row['user_name'],
                    password=PwdUtil.get_password_hash('123456'),
                    nickName=row['nick_name'],
                    email=row['email'],
                    phonenumber=str(row['phonenumber']),
                    sex=row['sex'],
                    status=row['status'],
                    createBy=current_user.user.user_name,
                    updateBy=current_user.user.user_name
                )
                user_info = UserDao.get_user_by_info(query_db, UserModel(userName=row['user_name']))
                if user_info:
                    if update_support:
                        edit_user = UserModel(
                            userId=user_info.user_id,
                            deptId=row['dept_id'],
                            userName=row['user_name'],
                            nickName=row['nick_name'],
                            email=row['email'],
                            phonenumber=str(row['phonenumber']),
                            sex=row['sex'],
                            status=row['status'],
                            updateBy=current_user.user.user_name
                        ).model_dump(exclude_unset=True)
                        UserDao.edit_user_dao(query_db, edit_user)
                    else:
                        add_error_result.append(f"{count}.用户账号{row['user_name']}已存在")
                else:
                    UserDao.add_user_dao(query_db, add_user)
            query_db.commit()
            result = dict(is_success=True, message='\n'.join(add_error_result))
        except Exception as e:
            query_db.rollback()
            raise e

        return CrudResponseModel(**result)

    @staticmethod
    def get_user_import_template_services():
        """
        获取用户导入模板service
        :return: 用户导入模板excel的二进制数据
        """
        header_list = ["部门编号", "登录名称", "用户名称", "用户邮箱", "手机号码", "用户性别", "帐号状态"]
        selector_header_list = ["用户性别", "帐号状态"]
        option_list = [{"用户性别": ["男", "女", "未知"]}, {"帐号状态": ["正常", "停用"]}]
        binary_data = get_excel_template(header_list=header_list, selector_header_list=selector_header_list,
                                         option_list=option_list)

        return binary_data

    @staticmethod
    def export_user_list_services(user_list: List):
        """
        导出用户信息service
        :param user_list: 用户信息列表
        :return: 用户信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            "userId": "用户编号",
            "userName": "用户名称",
            "nickName": "用户昵称",
            "deptName": "部门",
            "email": "邮箱地址",
            "phonenumber": "手机号码",
            "sex": "性别",
            "status": "状态",
            "createBy": "创建者",
            "createTime": "创建时间",
            "updateBy": "更新者",
            "updateTime": "更新时间",
            "remark": "备注",
        }

        data = user_list

        for item in data:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('sex') == '0':
                item['sex'] = '男'
            elif item.get('sex') == '1':
                item['sex'] = '女'
            else:
                item['sex'] = '未知'
        new_data = [{mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} for item in
                    data]

        binary_data = export_list2excel(new_data)

        return binary_data

    @classmethod
    def get_user_role_allocated_list_services(cls, query_db: Session, page_object: UserRoleQueryModel):
        """
        根据用户id获取已分配角色列表
        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 已分配角色列表
        """
        query_user = UserDao.get_user_detail_by_id(query_db, page_object.user_id)
        post_ids = ','.join([str(row.post_id) for row in query_user.get('user_post_info')])
        role_ids = ','.join([str(row.role_id) for row in query_user.get('user_role_info')])
        user = UserInfoModel(
            **CamelCaseUtil.transform_result(query_user.get('user_basic_info')),
            postIds=post_ids,
            roleIds=role_ids,
            dept=CamelCaseUtil.transform_result(query_user.get('user_dept_info')),
            role=CamelCaseUtil.transform_result(query_user.get('user_role_info'))
        )
        # row的属性与SelectedRoleModel的属性不完全一致：
        # 对于row中缺失的属性：如果SelectedRoleModel中对应的属性有默认值，那么在实例化时将使用这些默认值
        # 如果没有提供默认值且该属性是必需的（在构造函数中没有标记为Optional或没有其他默认值），那么在实例化时将会出现错误，因为构造函数期望这些参数被传递
        # 对于row中多余的属性：如果SelectedRoleModel的构造函数中包含了**kwargs来接受不限数量的额外关键字参数，
        # 那么这些额外的属性将被kwargs捕获，通常这些捕获到的额外属性不会被使用，除非在构造函数中有额外的逻辑来处理它们
        # 如果构造函数没有使用**kwargs，并且row中存在不是构造函数参数的额外字段，那么在尝试实例化SelectedRoleModel时会抛出TypeError，指出有多余的关键字参数

        # 获取所有可选角色列表
        query_role_list = [SelectedRoleModel(**row) for row in RoleService.get_role_select_option_services(query_db)]
        for model_a in query_role_list:  # 每个角色模型
            for model_b in user.role:  # 用户的每个角色
                if model_a.role_id == model_b.role_id:  # 对于用户已有的角色，在对应的SelectedRoleModel对象上设置flag属性为True
                    model_a.flag = True
        result = UserRoleResponseModel(
            roles=query_role_list,
            user=user
        )

        return result

    @classmethod
    def add_user_role_services(cls, query_db: Session, page_object: CrudUserRoleModel):
        """
        新增用户关联角色信息service（一个用户 - 多个角色 | 多个用户 - 一个角色）
        :param query_db: orm对象
        :param page_object: 新增用户关联角色对象
        :return: 新增用户关联角色校验结果
        """
        if page_object.user_id and page_object.role_ids:
            role_id_list = page_object.role_ids.split(',')
            try:
                for role_id in role_id_list:
                    user_role = cls.detail_user_role_services(query_db,
                                                              UserRoleModel(userId=page_object.user_id, roleId=role_id))
                    if user_role:  # 存在user_id、role_id的关联
                        continue
                    else:
                        UserDao.add_user_role_dao(query_db, UserRoleModel(userId=page_object.user_id, roleId=role_id))
                query_db.commit()
                result = dict(is_success=True, message='分配成功')
            except Exception as e:
                query_db.rollback()
                raise e
        # 不提供 role_ids 表示要取消该用户与所有角色的关联（意味着用户不应再有任何角色，防止用户拥有未明确授权的角色）
        elif page_object.user_id and not page_object.role_ids:
            try:
                UserDao.delete_user_role_by_user_and_role_dao(query_db, UserRoleModel(userId=page_object.user_id))
                query_db.commit()
                result = dict(is_success=True, message='分配成功')
            except Exception as e:
                query_db.rollback()
                raise e
        elif page_object.user_ids and page_object.role_id:
            # split 方法会基于提供的分隔符（在这种情况下是逗号 ,）来分割字符串。如果分隔符在字符串中不存在，则返回包含原始字符串的单元素列表
            # 确保了代码即便在处理单个用户ID时也能正常工作
            user_id_list = page_object.user_ids.split(',')
            try:
                for user_id in user_id_list:
                    user_role = cls.detail_user_role_services(query_db,
                                                              UserRoleModel(userId=user_id, roleId=page_object.role_id))
                    if user_role:
                        continue
                    else:
                        UserDao.add_user_role_dao(query_db, UserRoleModel(userId=user_id, roleId=page_object.role_id))
                query_db.commit()
                result = dict(is_success=True, message='新增成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='不满足新增条件')

        return CrudResponseModel(**result)

    @classmethod
    def delete_user_role_services(cls, query_db: Session, page_object: CrudUserRoleModel):
        """
        删除用户关联角色信息service（一/多个用户 - 一个角色）
        :param query_db: orm对象
        :param page_object: 删除用户关联角色对象
        :return: 删除用户关联角色校验结果
        """
        if (page_object.user_id and page_object.role_id) or (page_object.user_ids and page_object.role_id):
            if page_object.user_id and page_object.role_id:
                try:
                    UserDao.delete_user_role_by_user_and_role_dao(query_db, UserRoleModel(userId=page_object.user_id,
                                                                                          roleId=page_object.role_id))
                    query_db.commit()
                    result = dict(is_success=True, message='删除成功')
                except Exception as e:
                    query_db.rollback()
                    raise e
            elif page_object.user_ids and page_object.role_id:
                user_id_list = page_object.user_ids.split(',')
                try:
                    for user_id in user_id_list:
                        UserDao.delete_user_role_by_user_and_role_dao(query_db, UserRoleModel(userId=user_id,
                                                                                              roleId=page_object.role_id))
                    query_db.commit()
                    result = dict(is_success=True, message='删除成功')
                except Exception as e:
                    query_db.rollback()
                    raise e
            else:
                result = dict(is_success=False, message='不满足删除条件')
        else:
            result = dict(is_success=False, message='传入用户角色关联信息为空')

        return CrudResponseModel(**result)

    @classmethod
    def detail_user_role_services(cls, query_db: Session, page_object: UserRoleModel):
        """
        获取用户关联角色详细信息service
        :param query_db: orm对象
        :param page_object: 用户关联角色对象
        :return: 用户关联角色详细信息
        """
        user_role = UserDao.get_user_role_detail(query_db, page_object)

        return user_role
