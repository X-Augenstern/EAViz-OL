from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session
from module_admin.entity.do.user_do import SysUser, SysUserRole, SysUserPost
from module_admin.entity.do.role_do import SysRole, SysRoleMenu
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.post_do import SysPost
from module_admin.entity.do.menu_do import SysMenu
from module_admin.entity.vo.user_vo import *
from utils.page_util import PageUtil
from datetime import datetime, time


class UserDao:
    """
    用户管理模块数据库操作层
    """
    @classmethod
    def get_user_by_name(cls, db: Session, user_name: str):
        """
        根据 user_name 获取用户信息（正常、存在）
        :param db: orm对象
        :param user_name: 用户名
        :return: 当前用户名的用户信息对象
        """
        # 直到 first() 前所有步骤都在操作和返回一个 Query 对象
        # first()：从结果集中返回第一条记录（最新创建），如果查询结果为空，则返回 None，否则返回与查询结果相对应的 SysUser 实体的实例
        # 如果是 all()：返回与查询结果相对应的 SysUser 实体的实例 List
        # distinct()：查询结果中不会有重复的记录
        query_user_info = db.query(SysUser) \
            .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_name == user_name) \
            .order_by(desc(SysUser.create_time)).distinct().first()

        return query_user_info

    @classmethod
    def get_user_by_info(cls, db: Session, user: UserModel):
        """
        根据 UserModel.user_name 获取用户信息（存在）
        :param db: orm对象
        :param user: 用户参数
        :return: 当前用户参数的用户信息对象
        """
        query_user_info = db.query(SysUser) \
            .filter(SysUser.del_flag == 0,
                    SysUser.user_name == user.user_name) \
            .order_by(desc(SysUser.create_time)).distinct().first()

        return query_user_info

    @classmethod
    def get_user_by_id(cls, db: Session, user_id: int):
        """
        根据 user_id 获取用户信息（正常、存在）
        :param db: orm对象
        :param user_id: 用户id
        :return: 当前user_id的用户信息对象
        """
        query_user_basic_info = db.query(SysUser) \
            .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .distinct().first()

        # query(SysDept)：返回 SysDept 表中的数据
        # select_from(SysUser)：指定查询的起点为 SysUser 表
        # 把 SysDept 表内连接到 SysUser 表（一对一）
        # and_()：对应 MySQL 中的 AND，满足所有子条件的记录才会被选出 确保部门正常、存在
        # 连续使用 .filter() 方法时，默认就是 and_ 关系。例如，.filter(condition1).filter(condition2) 实际上是 and_(condition1, condition2)
        # 先用输入的 user_id 过滤 SysUser 表，再用 dept_id 去获取到 SysDept 表内容
        query_user_dept_info = db.query(SysDept).select_from(SysUser) \
            .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .join(SysDept, and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == 0, SysDept.del_flag == 0)) \
            .distinct().first()

        # outerjoin 默认左外连接：返回至少一个表中的所有记录，即使另一个表中没有匹配项
        # join 内连接：只返回两个表中联接字段完全匹配的记录。如果某个表中的行在另一个表中没有对应的匹配行，则这些行不会出现在查询结果中
        # 把 SysUserRole 表左外连接到 SysUser 表，确保 SysUser 表中的所有记录都会被包括在结果中，无论是否在 SysUserRole 表中有对应的角色信息（一对多）
        query_user_role_info = db.query(SysRole).select_from(SysUser) \
            .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id) \
            .join(SysRole, and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == 0, SysRole.del_flag == 0)) \
            .distinct().all()

        query_user_post_info = db.query(SysPost).select_from(SysUser) \
            .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .outerjoin(SysUserPost, SysUser.user_id == SysUserPost.user_id) \
            .join(SysPost, and_(SysUserPost.post_id == SysPost.post_id, SysPost.status == 0)) \
            .distinct().all()

        role_id_list = [item.role_id for item in query_user_role_info]
        if 1 in role_id_list:  # admin 获取全部正常的菜单
            query_user_menu_info = db.query(SysMenu) \
                .filter(SysMenu.status == 0) \
                .distinct().all()
        else:  # 其余用户获取相应的正常的菜单
            query_user_menu_info = db.query(SysMenu).select_from(SysUser) \
                .filter(SysUser.status == 0, SysUser.del_flag == 0, SysUser.user_id == user_id) \
                .outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id) \
                .outerjoin(SysRole,
                           and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == 0, SysRole.del_flag == 0)) \
                .outerjoin(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id) \
                .join(SysMenu, and_(SysRoleMenu.menu_id == SysMenu.menu_id, SysMenu.status == 0)) \
                .order_by(SysMenu.order_num) \
                .distinct().all()

        results = dict(  # 将结果用字典形式返回
            user_basic_info=query_user_basic_info,
            user_dept_info=query_user_dept_info,
            user_role_info=query_user_role_info,
            user_post_info=query_user_post_info,
            user_menu_info=query_user_menu_info
        )

        return results

    @classmethod
    def get_user_detail_by_id(cls, db: Session, user_id: int):
        """
        根据 user_id 获取用户详细信息（存在）
        :param db: orm对象
        :param user_id: 用户id
        :return: 当前user_id的用户信息对象
        """
        query_user_basic_info = db.query(SysUser) \
            .filter(SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .distinct().first()

        query_user_dept_info = db.query(SysDept).select_from(SysUser) \
            .filter(SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .join(SysDept, and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == 0, SysDept.del_flag == 0)) \
            .distinct().first()

        query_user_role_info = db.query(SysRole).select_from(SysUser) \
            .filter(SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id) \
            .join(SysRole, and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == 0, SysRole.del_flag == 0)) \
            .distinct().all()

        query_user_post_info = db.query(SysPost).select_from(SysUser) \
            .filter(SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .outerjoin(SysUserPost, SysUser.user_id == SysUserPost.user_id) \
            .join(SysPost, and_(SysUserPost.post_id == SysPost.post_id, SysPost.status == 0)) \
            .distinct().all()

        query_user_menu_info = db.query(SysMenu).select_from(SysUser) \
            .filter(SysUser.del_flag == 0, SysUser.user_id == user_id) \
            .outerjoin(SysUserRole, SysUser.user_id == SysUserRole.user_id) \
            .outerjoin(SysRole,
                       and_(SysUserRole.role_id == SysRole.role_id, SysRole.status == 0, SysRole.del_flag == 0)) \
            .outerjoin(SysRoleMenu, SysRole.role_id == SysRoleMenu.role_id) \
            .join(SysMenu, and_(SysRoleMenu.menu_id == SysMenu.menu_id, SysMenu.status == 0)) \
            .distinct().all()

        results = dict(
            user_basic_info=query_user_basic_info,
            user_dept_info=query_user_dept_info,
            user_role_info=query_user_role_info,
            user_post_info=query_user_post_info,
            user_menu_info=query_user_menu_info
        )

        return results

    @classmethod
    def get_user_list(cls, db: Session, query_object: UserPageQueryModel, data_scope_sql: str, is_page: bool = False):
        """
        根据查询参数获取用户列表信息
        :param db: orm对象
        :param query_object: 查询参数对象
        :param data_scope_sql: 数据权限对应的查询sql语句
        :param is_page: 是否开启分页
        :return: 用户列表信息对象
        """
        # 同时获取 SysUser 与 SysDept 表数据
        # 多个通过 .filter() 方法传递的条件是以逻辑 AND 的方式连接的

        # or_()：对应 MySQL 中的 OR，返回所有满足至少一个条件的结果，直接属于该部门的用户以及属于该部门所有子部门的用户
        # in_()：对应 MySQL 中的 IN，匹配多个可能的值
        # like()：对应 MySQL 中的 LIKE，模糊查询
        # between()：对应 MySQL 中的 BETWEEN，检查某个字段的值是否位于两个值之间（包含这两个值）

        # func.find_in_set() 是对 MySQL 中的 FIND_IN_SET() 函数的调用：查找字符串列表（由逗号分隔）中的一个字符串，并返回其位置（从1开始的索引）。如果没有找到，它返回0
        # ancestors = "1,2,3,4"，可以使用 FIND_IN_SET(3, ancestors) 来检查特定的 ID '3' 是否在这个列表中，以及它的位置： return 3
        # MySQL 会自动将传入的 3 转为 '3'
        # 如果 find_in_set 返回的是 0，表示 query_object.dept_id 没有在 SysDept.ancestors 中找到，此时结果为 False，对应的记录不会被选出
        # 如果 find_in_set 返回的是一个大于 0 的值，表示找到了 query_object.dept_id 在 SysDept.ancestors 中的位置，此时结果为 True，对应的记录会被选出
        # 如果 query_object.dept_id 有值，根据规则执行过滤；否则默认为 True，即不会对查询结果产生任何过滤效果（所有记录都会被选出）

        # like(f'%{query_object.user_name}%') 匹配任何包含 query_object.user_name 作为子字符串的 user_name

        # datetime.strptime(query_object.begin_time, '%Y-%m-%d') 将字符串格式的日期（假设格式为 'YYYY-MM-DD'）解析为 datetime 对象
        # datetime.combine() 将解析得到的日期与 time(00, 00, 00) 结合，表示该天的开始时刻（午夜开始）
        # 从 SysUser 表中过滤出创建时间在指定的开始日期的午夜和结束日期的最后一分钟之间的所有用户

        # eval()：执行一个字符串表达式，并返回表达式的值
        # eval(data_scope_sql) 表示执行由 data_scope_sql 字符串所表示的 Python 代码或表达式。为了动态地控制查询的数据范围，比如根据用户的权限来限制数据的访问。
        # 如 "SysUser.id > 10"。这种方式允许根据不同的情况灵活地修改查询条件

        # distinct()、filter()、outerjoin()这些查询方法都一样，返回的是一个查询对象，而不是结果集本身
        # 要从这个查询对象中获取实际的数据，需要使用一个执行查询的方法：all()、first()、one()
        query = db.query(SysUser, SysDept) \
            .filter(SysUser.del_flag == 0,
                    or_(SysUser.dept_id == query_object.dept_id, SysUser.dept_id.in_(
                        db.query(SysDept.dept_id).filter(func.find_in_set(query_object.dept_id, SysDept.ancestors))
                    )) if query_object.dept_id else True,
                    SysUser.user_name.like(f'%{query_object.user_name}%') if query_object.user_name else True,
                    SysUser.nick_name.like(f'%{query_object.nick_name}%') if query_object.nick_name else True,
                    SysUser.email.like(f'%{query_object.email}%') if query_object.email else True,
                    SysUser.phonenumber.like(f'%{query_object.phonenumber}%') if query_object.phonenumber else True,
                    SysUser.status == query_object.status if query_object.status else True,
                    SysUser.sex == query_object.sex if query_object.sex else True,
                    SysUser.create_time.between(
                        datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                        datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)))
                    if query_object.begin_time and query_object.end_time else True,
                    eval(data_scope_sql)
                    ) \
            .outerjoin(SysDept, and_(SysUser.dept_id == SysDept.dept_id, SysDept.status == 0, SysDept.del_flag == 0)) \
            .distinct()

        user_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return user_list

    @classmethod
    def add_user_dao(cls, db: Session, user: UserModel):
        """
        新增用户数据库操作
        :param db: orm对象
        :param user: 用户对象
        :return: 新增校验结果
        """
        # user.model_dump(exclude={'admin'})：获取 user 对象的数据字典形式并排除字典中的 'admin' 键
        # ** 一种参数解包的语法，将字典中的键值对转化为函数或类构造函数的命名参数
        # 用 user.model_dump() 返回的字典（不包含 'admin' 键）作为参数来创建一个新的 SysUser 类的实例
        db_user = SysUser(**user.model_dump(exclude={'admin'}))
        db.add(db_user)  # 将 db_user 对象添加到数据库会话中。这一步骤并不会立即执行数据库操作，而是将对象标记为待添加，等待后续的提交或进一步操作
        # 确保所有挂起的更改（如插入、更新、删除）立即生效，这样数据库会生成并分配相应的主键值（如 user_id），并将其更新到 db_user 对象中
        # 因此，调用 flush 后，db_user 对象会包含数据库分配的 user_id
        db.flush()

        return db_user  # 将新创建的 db_user 对象返回。此时，该对象已与数据库同步，具有数据库分配的任何默认值或ID

    @classmethod
    def edit_user_dao(cls, db: Session, user: dict):
        """
        编辑用户数据库操作
        :param db: orm对象
        :param user: 需要更新的用户字典
        :return: 编辑校验结果
        """
        # update() 是 SQLAlchemy ORM 提供的一个功能，它允许直接传入一个字典，并将字典中的键值对应用到满足过滤条件的数据库记录上。
        # 在这个字典中，键应该与数据库模型中的属性名称相匹配，值则是希望更新的新值
        # 当调用 .update(user) 方法时，ORM 会将字典中的键映射到数据库表的列名上，生成相应的 SQL UPDATE 语句，将每个字典键对应的列更新为新的值
        # 只有那些在字典中出现的键会被更新，未提及的列将保持不变；如果字典中存在一些键在数据库表的模型定义中不存在，这些额外的键将被忽略，不会影响数据库操作
        db.query(SysUser) \
            .filter(SysUser.user_id == user.get('user_id')) \
            .update(user)

    @classmethod
    def delete_user_dao(cls, db: Session, user: UserModel):
        """
        删除用户数据库操作
        :param db: orm对象
        :param user: 用户对象
        """
        db.query(SysUser) \
            .filter(SysUser.user_id == user.user_id) \
            .update({SysUser.del_flag: '2', SysUser.update_by: user.update_by, SysUser.update_time: user.update_time})

    @classmethod
    def get_user_role_allocated_list_by_user_id(cls, db: Session, query_object: UserRoleQueryModel):
        """
        根据用户id获取用户已分配的角色列表信息数据库操作
        :param db: orm对象
        :param query_object: 用户角色查询对象
        :return: 用户已分配的角色列表信息
        """
        allocated_role_list = db.query(SysRole) \
            .filter(
            SysRole.del_flag == 0,
            SysRole.role_id != 1,
            SysRole.role_id.in_(
                db.query(SysUserRole.role_id).filter(SysUserRole.user_id == query_object.user_id)
            )
        ).distinct().all()

        return allocated_role_list

    @classmethod
    def get_user_role_allocated_list_by_role_id(cls, db: Session, query_object: UserRolePageQueryModel,
                                                is_page: bool = False):
        """
        根据角色id获取角色已分配的用户列表信息
        :param db: orm对象
        :param query_object: 用户角色查询对象
        :param is_page: 是否开启分页
        :return: 角色已分配的用户列表信息
        """
        query = db.query(SysUser) \
            .filter(
            SysUser.del_flag == 0,
            SysUser.user_id != 1,
            SysUser.user_name == query_object.user_name if query_object.user_name else True,
            SysUser.phonenumber == query_object.phonenumber if query_object.phonenumber else True,
            SysUser.user_id.in_(
                db.query(SysUserRole.user_id).filter(SysUserRole.role_id == query_object.role_id)
            )
        ).distinct()

        allocated_user_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return allocated_user_list

    @classmethod
    def get_user_role_unallocated_list_by_role_id(cls, db: Session, query_object: UserRolePageQueryModel,
                                                  is_page: bool = False):
        """
        根据角色id获取未分配的用户列表信息
        :param db: orm对象
        :param query_object: 用户角色查询对象
        :param is_page: 是否开启分页
        :return: 角色未分配的用户列表信息
        """
        # ~ 对应 SQL 中的 NOT 关键字
        # SELECT * FROM SysUser WHERE user_id NOT IN (SELECT user_id FROM SysUserRole WHERE role_id = [某个角色ID])
        query = db.query(SysUser) \
            .filter(
            SysUser.del_flag == 0,
            SysUser.user_id != 1,
            SysUser.user_name == query_object.user_name if query_object.user_name else True,
            SysUser.phonenumber == query_object.phonenumber if query_object.phonenumber else True,
            ~SysUser.user_id.in_(
                db.query(SysUserRole.user_id).filter(SysUserRole.role_id == query_object.role_id)
            )
        ).distinct()

        unallocated_user_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return unallocated_user_list

    @classmethod
    def add_user_role_dao(cls, db: Session, user_role: UserRoleModel):
        """
        新增用户角色关联信息数据库操作
        :param db: orm对象
        :param user_role: 用户角色关联对象
        """
        db_user_role = SysUserRole(**user_role.model_dump())
        db.add(db_user_role)

    @classmethod
    def delete_user_role_dao(cls, db: Session, user_role: UserRoleModel):
        """
        删除用户角色关联信息数据库操作
        :param db: orm对象
        :param user_role: 用户角色关联对象
        """
        db.query(SysUserRole) \
            .filter(SysUserRole.user_id == user_role.user_id) \
            .delete()

    @classmethod
    def delete_user_role_by_user_and_role_dao(cls, db: Session, user_role: UserRoleModel):
        """
        根据用户id及角色id删除用户角色关联信息数据库操作
        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return:
        """
        db.query(SysUserRole) \
            .filter(SysUserRole.user_id == user_role.user_id,
                    SysUserRole.role_id == user_role.role_id if user_role.role_id else True) \
            .delete()

    @classmethod
    def get_user_role_detail(cls, db: Session, user_role: UserRoleModel):
        """
        根据用户角色关联获取用户角色关联详细信息
        :param db: orm对象
        :param user_role: 用户角色关联对象
        :return: 用户角色关联信息
        """
        user_role_info = db.query(SysUserRole) \
            .filter(SysUserRole.user_id == user_role.user_id, SysUserRole.role_id == user_role.role_id) \
            .distinct().first()

        return user_role_info

    @classmethod
    def add_user_post_dao(cls, db: Session, user_post: UserPostModel):
        """
        新增用户岗位关联信息数据库操作
        :param db: orm对象
        :param user_post: 用户岗位关联对象
        """
        db_user_post = SysUserPost(**user_post.model_dump())
        db.add(db_user_post)

    @classmethod
    def delete_user_post_dao(cls, db: Session, user_post: UserPostModel):
        """
        删除用户岗位关联信息数据库操作
        :param db: orm对象
        :param user_post: 用户岗位关联对象
        """
        db.query(SysUserPost) \
            .filter(SysUserPost.user_id == user_post.user_id) \
            .delete()
