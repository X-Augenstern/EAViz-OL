from collections.abc import Generator
from contextlib import contextmanager
from sqlalchemy.orm import Session
from typing import Optional

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
    current_db = SessionLocal()  # 行1：创建 Session 实例，打开会话
    try:
        yield current_db  # 行2：暂停函数的执行并将当前的数据库会话对象 Session 返回给调用者，一旦调用者完成操作，控制权会返回到这个函数中
    finally:
        current_db.close()  # 行3：生成器耗尽后执行，关闭 Session


get_db = get_db_pro  # 指向 get_db_pro 函数的引用，可以被调用来生成和 get_db_pro 相同的结果


# @contextmanager 会把函数包装成「上下文管理器」，而这个函数本身是生成器函数（因为里面有 yield）；
# 生成器函数的返回类型应该是 Generator[产出类型, 发送类型, 返回类型]，这里「产出 Session 实例、不接收发送值、最终无返回」，
# 所以类型应该是 Generator[Session, None, None]
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    定时任务专用：获取数据库会话（上下文管理器）
    替代 Depends(get_db)，手动处理生成器解析和 Session 关闭
    """
    # 步骤1：调用 get_db_pro() → 仅返回生成器对象，get_db_pro 函数体一行都不执行！
    db_generate = get_db_pro()
    db_session: Optional[Session] = None
    try:
        # 模拟 Depends 的核心逻辑
        # 步骤2：执行 next(db_generate) → 开始真正执行 get_db_pro 的函数体：
        # 1. 先执行 get_db_pro 的「行1」：current_db = SessionLocal()（创建 Session）；
        # 2. 进入 get_db_pro 的 try 块；
        # 3. 执行到 get_db_pro 的「行2」：yield current_db → 暂停执行！
        #    - 把 current_db 作为 next() 的返回值，赋值给 db_session；
        #    - get_db_pro 的执行停在 yield 这一行，不会继续往下走（不会执行 close()）；
        db_session = next(db_generate)
        yield db_session  # 把 Session 交给 with 语句使用
    except Exception as e:
        # 异常时回滚（和接口逻辑对齐）
        if db_session is not None:
            db_session.rollback()
        raise e  # 抛出异常供上层处理
    finally:
        # 步骤3：再次执行 next(db_generate)，get_db_pro 才会从 yield 这一行继续往下走，最终执行 finally 里的 close()
        # yield 是「暂停键」，next() 是「生成器的执行开关」，第一次 next() 是「启动并拿到 Session」，第二次 next() 是「收尾并关闭 Session」
        try:
            next(db_generate)
        except StopIteration:
            pass  # 生成器耗尽是正常的，忽略
