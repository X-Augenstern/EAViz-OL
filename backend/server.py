from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from utils.log_util import logger
from config.env import AppConfig
from config.env import EAVizConfig
from config.get_db import init_create_table
from config.get_redis import RedisUtil
from config.get_scheduler import SchedulerUtil
from config.get_model import ModelUtil
from fastapi import FastAPI
from sub_applications.handle import handle_sub_applications
from middlewares.handle import handle_middleware
from exceptions.handle import handle_exception
from module_admin.controller.login_controller import loginController
from module_admin.controller.captcha_controller import captchaController
from module_admin.controller.user_controller import userController
from module_admin.controller.menu_controller import menuController
from module_admin.controller.dept_controller import deptController
from module_admin.controller.role_controller import roleController
from module_admin.controller.post_controler import postController
from module_admin.controller.dict_controller import dictController
from module_admin.controller.config_controller import configController
from module_admin.controller.notice_controller import noticeController
from module_admin.controller.log_controller import logController
from module_admin.controller.edf_controller import edfController
from module_admin.controller.video_controller import videoController
from module_admin.controller.online_controller import onlineController
from module_admin.controller.job_controller import jobController
from module_admin.controller.server_controller import serverController
from module_admin.controller.cache_controller import cacheController
from module_admin.controller.common_controller import commonController
from module_admin.controller.analysis_controller import analysisController


# from utils.common_util import worship


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    生命周期事件
    """
    logger.info(f"{AppConfig.app_name}开始启动")
    # worship()
    await init_create_table()
    """
    在 FastAPI 中，app.state 是一个用于存储全局状态的属性，可以在其中存储任意对象（本质是字典对象），如数据库连接、缓存、配置等。
    app.state 之所以可以有 .redis 属性，是因为在应用启动时，手动添加了这个属性。
    FastAPI 本身没有预定义的 .redis 属性，这个属性是可以动态添加的。
    """
    app.state.redis = await RedisUtil.create_redis_pool()
    await RedisUtil.init_sys_dict(app.state.redis)
    await RedisUtil.init_sys_config(app.state.redis)
    await SchedulerUtil.init_system_scheduler()
    app.state.models = await ModelUtil.init_models()
    # 初始化全局线程池执行器用于视频处理（CPU/GPU密集型任务）
    # 使用线程池而不是进程池，因为PyTorch模型通常在同一进程内共享更高效
    # max_workers可以根据服务器配置调整，建议为CPU核心数或GPU数量
    app.state.vd_executor = ThreadPoolExecutor(max_workers=EAVizConfig.VDConfig.VD_EXECUTOR_MAX_WORKERS,
                                               thread_name_prefix="vd_processor")
    logger.info(f"VD视频处理线程池已初始化，最大并发数: {EAVizConfig.VDConfig.VD_EXECUTOR_MAX_WORKERS}")

    logger.info(f"{AppConfig.app_name}启动成功")
    yield
    await RedisUtil.close_redis_pool(app)
    await SchedulerUtil.close_system_scheduler()
    # 关闭线程池
    if hasattr(app.state, 'vd_executor'):
        app.state.vd_executor.shutdown(wait=True)
        logger.info("VD视频处理线程池已关闭")


# 初始化FastAPI对象
app = FastAPI(
    title=AppConfig.app_name,
    description=f'{AppConfig.app_name}接口文档',
    version=AppConfig.app_version,
    lifespan=lifespan
)

# 挂载子应用
handle_sub_applications(app)
# 加载中间件处理方法
handle_middleware(app)
# 加载全局异常处理方法
handle_exception(app)

# 加载路由列表
controller_list = [
    {'router': loginController, 'tags': ['登录模块']},
    {'router': captchaController, 'tags': ['验证码模块']},
    {'router': userController, 'tags': ['系统管理-用户管理']},
    {'router': roleController, 'tags': ['系统管理-角色管理']},
    {'router': menuController, 'tags': ['系统管理-菜单管理']},
    {'router': deptController, 'tags': ['系统管理-部门管理']},
    {'router': postController, 'tags': ['系统管理-岗位管理']},
    {'router': dictController, 'tags': ['系统管理-字典管理']},
    {'router': configController, 'tags': ['系统管理-参数管理']},
    {'router': noticeController, 'tags': ['系统管理-通知公告管理']},
    {'router': logController, 'tags': ['系统管理-日志管理']},
    {'router': edfController, 'tags': ['系统管理-EDF管理']},
    {'router': videoController, 'tags': ['系统管理-视频管理']},
    {'router': onlineController, 'tags': ['系统监控-在线用户']},
    {'router': jobController, 'tags': ['系统监控-定时任务']},
    {'router': serverController, 'tags': ['系统监控-菜单管理']},
    {'router': cacheController, 'tags': ['系统监控-缓存监控']},
    {'router': commonController, 'tags': ['通用模块']},
    {'router': analysisController, 'tags': ['智能分析模块']}
]

for controller in controller_list:
    app.include_router(router=controller.get('router'), tags=controller.get('tags'))
