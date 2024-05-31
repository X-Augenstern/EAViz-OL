from fastapi import APIRouter, Request
from fastapi import Depends
from config.get_db import get_db
from module_admin.service.login_service import LoginService
from module_admin.service.menu_service import *
from utils.response_util import *
from utils.log_util import *
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.annotation.log_annotation import log_decorator

menuController = APIRouter(prefix='/system/menu', dependencies=[Depends(LoginService.get_current_user)])


@menuController.get("/treeselect")
async def get_system_menu_tree(request: Request, query_db: Session = Depends(get_db),
                               current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取当前用户的菜单树
    """
    try:
        menu_query_result = MenuService.get_menu_tree_services(query_db, current_user)
        logger.info('获取成功')
        return ResponseUtil.success(data=menu_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.get("/roleMenuTreeselect/{role_id}")
async def get_system_role_menu_tree(request: Request, role_id: int, query_db: Session = Depends(get_db),
                                    current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取当前用户的菜单树以及角色菜单关联列表信息
    """
    try:
        role_menu_query_result = MenuService.get_role_menu_tree_services(query_db, role_id, current_user)
        logger.info('获取成功')
        return ResponseUtil.success(model_content=role_menu_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.get("/list", response_model=List[MenuModel],
                    dependencies=[Depends(CheckUserInterfaceAuth('system:menu:list'))])
async def get_system_menu_list(request: Request, menu_query: MenuQueryModel = Depends(MenuQueryModel.as_query),
                               query_db: Session = Depends(get_db),
                               current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取当前用户菜单列表
    """
    try:
        menu_query_result = MenuService.get_menu_list_services(query_db, menu_query, current_user)
        logger.info('获取成功')
        return ResponseUtil.success(data=menu_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.post("", dependencies=[Depends(CheckUserInterfaceAuth('system:menu:add'))])
@log_decorator(title='菜单管理', business_type=1)
async def add_system_menu(request: Request, add_menu: MenuModel, query_db: Session = Depends(get_db),
                          current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    新增菜单
    """
    try:
        add_menu.create_by = current_user.user.user_name
        add_menu.update_by = current_user.user.user_name
        add_menu_result = MenuService.add_menu_services(query_db, add_menu)
        if add_menu_result.is_success:
            logger.info(add_menu_result.message)
            return ResponseUtil.success(msg=add_menu_result.message)
        else:
            logger.warning(add_menu_result.message)
            return ResponseUtil.failure(msg=add_menu_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.put("", dependencies=[Depends(CheckUserInterfaceAuth('system:menu:edit'))])
@log_decorator(title='菜单管理', business_type=2)
async def edit_system_menu(request: Request, edit_menu: MenuModel, query_db: Session = Depends(get_db),
                           current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    修改菜单
    """
    try:
        edit_menu.update_by = current_user.user.user_name
        edit_menu.update_time = datetime.now()
        edit_menu_result = MenuService.edit_menu_services(query_db, edit_menu)
        if edit_menu_result.is_success:
            logger.info(edit_menu_result.message)
            return ResponseUtil.success(msg=edit_menu_result.message)
        else:
            logger.warning(edit_menu_result.message)
            return ResponseUtil.failure(msg=edit_menu_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.delete("/{menu_ids}", dependencies=[Depends(CheckUserInterfaceAuth('system:menu:remove'))])
@log_decorator(title='菜单管理', business_type=3)
async def delete_system_menu(request: Request, menu_ids: str, query_db: Session = Depends(get_db)):
    """
    删除菜单

    注意区分路径参数和查询参数：

    在路由定义中使用 {menu_ids} 来表示路径参数，这意味着 URL 中该部分的值将被提取并传递给路径操作函数的 menu_ids 参数。
    例如，发送请求到 /system/menu/123,456,789，menu_ids 将接收字符串 "123,456,789"。
    FastAPI 会自动将路径参数从 URL 中提取，并传递给对应的路径操作函数中的参数。这不需要显式地定义为 Query 参数。

    因为路径参数和查询参数是不同的概念：
    路径参数：在 URL 路径中定义，如 /{menu_ids}。
    查询参数：在 URL 中 ? 后面定义，如 ?menu_ids=123,456,789，需要使用 Query 进行显式声明。
    """

    """
    路径参数
    定义与用途
    定义：路径参数在URL路径的一部分中，通过占位符表示，例如/items/{item_id}。
    用途：路径参数通常用于标识资源的唯一标识符。这些参数是URL路径的一部分，通常用于访问特定资源。
    示例：
        获取特定用户的信息：GET /users/{user_id}
        删除特定的菜单项：DELETE /menus/{menu_id}
    语法：
    在FastAPI中通过路径定义，e. g.：
    @app.get("/users/{user_id}")
    async def read_user(user_id: int):
        return {"user_id": user_id}
    -> GET /users/123
        
    查询参数
    定义与用途
    定义：查询参数位于URL路径后的问号?之后，通过键值对表示，例如/items?item_id=123。
    用途：查询参数通常用于筛选、排序或分页等操作，它们可以用于提供附加信息，而不改变资源的基础路径。
    示例：
        获取特定条件的用户列表：GET /users?age=30&city=NewYork
        获取分页的菜单项：GET /menus?page=2&size=10
    语法：
    在FastAPI中通过Query定义，e. g.：
    @app.get("/users")
    async def read_users(age: int = Query(None), city: str = Query(None)):
        return {"age": age, "city": city}
    -> GET /users?age=30&city=NewYork
    
    组合使用，e. g.:
    @app.get("/users/{user_id}/items")
    async def read_user_items(user_id: int, page: int = Query(1), size: int = Query(10)):
        return {"user_id": user_id, "page": page, "size": size}
    -> GET /users/123/items?page=2&size=5
        
    具体区别
    位置与形式：
    路径参数：是URL路径的一部分，例如/items/{item_id}。
    查询参数：位于URL路径后的问号?之后，例如/items?item_id=123。
    
    语义与用途：
    路径参数：用于标识唯一资源，通常用于RESTful API中资源的标识符。
    查询参数：用于过滤、排序、分页等操作，不用于标识唯一资源。
    
    定义方式：
    路径参数：在路径字符串中通过占位符定义。
    查询参数：在路径操作函数中通过函数参数或使用Query类定义。
    
    可选性：
    路径参数：通常是必须的，因为它们是URL路径的一部分。
    查询参数：通常是可选的，可以有默认值。
    """
    try:
        delete_menu = DeleteMenuModel(menuIds=menu_ids)
        delete_menu_result = MenuService.delete_menu_services(query_db, delete_menu)
        if delete_menu_result.is_success:
            logger.info(delete_menu_result.message)
            return ResponseUtil.success(msg=delete_menu_result.message)
        else:
            logger.warning(delete_menu_result.message)
            return ResponseUtil.failure(msg=delete_menu_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@menuController.get("/{menu_id}", response_model=MenuModel,
                    dependencies=[Depends(CheckUserInterfaceAuth('system:menu:query'))])
async def query_detail_system_menu(request: Request, menu_id: int, query_db: Session = Depends(get_db)):
    """
    根据菜单id获取详细信息
    """
    try:
        menu_detail_result = MenuService.menu_detail_services(query_db, menu_id)
        logger.info(f'获取menu_id为{menu_id}的信息成功')
        return ResponseUtil.success(data=menu_detail_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
