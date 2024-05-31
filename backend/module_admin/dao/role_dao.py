from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from module_admin.entity.do.role_do import SysRole, SysRoleMenu, SysRoleDept
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.vo.role_vo import *
from utils.page_util import PageUtil
from datetime import datetime, time


class RoleDao:
    """
    角色管理模块数据库操作层
    """
    @classmethod
    def get_role_by_name(cls, db: Session, role_name: str):
        """
        根据角色名获取在用角色信息
        :param db: orm对象
        :param role_name: 角色名
        :return: 当前角色名的角色信息对象
        """
        query_role_info = db.query(SysRole) \
            .filter(SysRole.status == 0, SysRole.del_flag == 0, SysRole.role_name == role_name) \
            .order_by(desc(SysRole.create_time)).distinct().first()

        return query_role_info

    @classmethod
    def get_role_by_info(cls, db: Session, role: RoleModel):
        """
        根据角色参数获取角色信息
        :param db: orm对象
        :param role: 角色参数
        :return: 当前角色参数的角色信息对象
        """
        query_role_info = db.query(SysRole) \
            .filter(SysRole.del_flag == 0,
                    SysRole.role_name == role.role_name if role.role_name else True,
                    SysRole.role_key == role.role_key if role.role_key else True) \
            .order_by(desc(SysRole.create_time)).distinct().first()

        return query_role_info

    @classmethod
    def get_role_by_id(cls, db: Session, role_id: int):
        """
        根据角色id获取在用角色信息
        :param db: orm对象
        :param role_id: 角色id
        :return: 当前角色id的角色信息对象
        """
        role_info = db.query(SysRole) \
            .filter(SysRole.role_id == role_id, SysRole.status == 0, SysRole.del_flag == 0) \
            .first()

        return role_info

    @classmethod
    def get_role_detail_by_id(cls, db: Session, role_id: int):
        """
        根据role_id获取角色详细信息
        :param db: orm对象
        :param role_id: 角色id
        :return: 当前role_id的角色信息对象
        """
        query_role_info = db.query(SysRole) \
            .filter(SysRole.del_flag == 0, SysRole.role_id == role_id) \
            .distinct().first()

        return query_role_info

    @classmethod
    def get_role_select_option_dao(cls, db: Session):
        """
        获取编辑页面对应的在用角色列表信息
        :param db: orm对象
        :return: 角色列表信息
        """
        role_info = db.query(SysRole) \
            .filter(SysRole.role_id != 1, SysRole.status == 0, SysRole.del_flag == 0) \
            .all()

        return role_info

    @classmethod
    def get_role_list(cls, db: Session, query_object: RolePageQueryModel, is_page: bool = False):
        """
        根据查询参数获取角色列表信息
        :param db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 角色列表信息对象
        """
        query = db.query(SysRole) \
            .filter(SysRole.del_flag == 0,
                    SysRole.role_name.like(f'%{query_object.role_name}%') if query_object.role_name else True,
                    SysRole.role_key.like(f'%{query_object.role_key}%') if query_object.role_key else True,
                    SysRole.status == query_object.status if query_object.status else True,
                    SysRole.create_time.between(
                        datetime.combine(datetime.strptime(query_object.begin_time, '%Y-%m-%d'), time(00, 00, 00)),
                        datetime.combine(datetime.strptime(query_object.end_time, '%Y-%m-%d'), time(23, 59, 59)))
                    if query_object.begin_time and query_object.end_time else True
                    ) \
            .order_by(SysRole.role_sort) \
            .distinct()

        role_list = PageUtil.paginate(query, query_object.page_num, query_object.page_size, is_page)

        return role_list

    @classmethod
    def add_role_dao(cls, db: Session, role: RoleModel):
        """
        新增角色数据库操作
        :param db: orm对象
        :param role: 角色对象
        """
        db_role = SysRole(**role.model_dump(exclude={'admin'}))
        db.add(db_role)
        db.flush()

        return db_role

    @classmethod
    def edit_role_dao(cls, db: Session, role: dict):
        """
        编辑角色数据库操作
        :param db: orm对象
        :param role: 需要更新的角色字典
        """
        db.query(SysRole) \
            .filter(SysRole.role_id == role.get('role_id')) \
            .update(role)

    @classmethod
    def delete_role_dao(cls, db: Session, role: RoleModel):
        """
        删除角色数据库操作
        :param db: orm对象
        :param role: 角色对象
        """
        db.query(SysRole) \
            .filter(SysRole.role_id == role.role_id) \
            .update({SysRole.del_flag: '2', SysRole.update_by: role.update_by, SysRole.update_time: role.update_time})

    @classmethod
    def get_role_menu_dao(cls, db: Session, role_id: int):
        """
        根据角色id获取角色菜单关联列表信息
        :param db: orm对象
        :param role_id: 角色id
        :return: 角色菜单关联列表信息
        """
        role_menu_query_all = db.query(SysRoleMenu) \
            .filter(SysRoleMenu.role_id == role_id) \
            .distinct().all()

        return role_menu_query_all

    @classmethod
    def add_role_menu_dao(cls, db: Session, role_menu: RoleMenuModel):
        """
        新增角色菜单关联信息数据库操作
        :param db: orm对象
        :param role_menu: 用户角色菜单关联对象
        """
        db_role_menu = SysRoleMenu(**role_menu.model_dump())
        db.add(db_role_menu)

    @classmethod
    def delete_role_menu_dao(cls, db: Session, role_menu: RoleMenuModel):
        """
        删除角色菜单关联信息数据库操作
        :param db: orm对象
        :param role_menu: 角色菜单关联对象
        """
        db.query(SysRoleMenu) \
            .filter(SysRoleMenu.role_id == role_menu.role_id) \
            .delete()

    @classmethod
    def get_role_dept_dao(cls, db: Session, role_id: int):
        """
        根据角色id获取角色部门关联列表信息
        :param db: orm对象
        :param role_id: 角色id
        :return: 角色部门关联列表信息
        """
        # EXISTS 是一个子查询操作符，用来测试子查询是否返回至少一个行。如果返回至少一个行，则 EXISTS 表达式的结果为 True；如果没有返回任何行，则结果为 False。
        # 一般配合 WHERE 子句一同使用。如果 EXISTS 函数返回 True，那么 WHERE 子句中的条件将被满足，相应的记录将被包含在结果集中
        # .exists()会检查是否有任何满足前述条件的 SysDept 记录存在
        # ~ 反转 .exists() 的结果。如果子查询找到匹配的记录，则 .exists() 返回 True，否定后变为 False；如果没有找到，则返回 False，否定后变为 True
        # 查找与 role_id 关联的最底层部门（不作为任何部门的祖先）
        role_dept_query_all = db.query(SysRoleDept) \
            .filter(SysRoleDept.role_id == role_id,
                    ~db.query(SysDept).filter(func.find_in_set(SysRoleDept.dept_id, SysDept.ancestors)).exists()
                    ) \
            .distinct().all()

        return role_dept_query_all

    @classmethod
    def add_role_dept_dao(cls, db: Session, role_dept: RoleDeptModel):
        """
        新增角色部门关联信息数据库操作
        :param db: orm对象
        :param role_dept: 用户角色部门关联对象
        """
        db_role_dept = SysRoleDept(**role_dept.model_dump())
        db.add(db_role_dept)

    @classmethod
    def delete_role_dept_dao(cls, db: Session, role_dept: RoleDeptModel):
        """
        删除角色部门关联信息数据库操作
        :param db: orm对象
        :param role_dept: 角色部门关联对象
        """
        db.query(SysRoleDept) \
            .filter(SysRoleDept.role_id == role_dept.role_id) \
            .delete()
