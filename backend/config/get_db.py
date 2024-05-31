from config.database import *
from utils.log_util import logger


async def init_create_table():
    """
    应用启动时初始化数据库连接
    """
    logger.info("初始化数据库连接...")
    # 根据定义的模型自动创建数据库表。Base 中包含了所有继承了该基类的模型的元数据
    Base.metadata.create_all(bind=engine)  # 通过指定的 engine（数据库引擎）来连接数据库，并根据模型定义创建所有尚未存在的表。这样可以确保所需要的表在数据库中已经被创建好。
    logger.info("数据库连接成功")


def get_db_pro():
    """
    生成器对象：每一个请求处理完毕后会关闭当前连接，不同的请求使用不同的连接
    """
    current_db = SessionLocal()  # 打开会话
    try:
        yield current_db  # 暂停函数的执行并将当前的数据库会话对象返回给调用者，一旦调用者完成操作，控制权会返回到这个函数中
    finally:
        current_db.close()  # 关闭会话


get_db = get_db_pro  # 指向 get_db_pro 函数的引用，可以被调用来生成和 get_db_pro 相同的结果
