from apscheduler.events import EVENT_ALL
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from importlib import import_module
from json import loads, dumps

from config.database import engine, SQLALCHEMY_DATABASE_URL, SessionLocal
from config.env import RedisConfig
from module_admin.dao.job_dao import Session, JobDao
from module_admin.service.job_log_service import JobLogService, JobLogModel
from utils.log_util import logger


# 任务调度器(Scheduler)：配置作业存储器和执行器可以在调度器中完成，例如添加、修改和移除作业。
# 作业存储(Job Store)：任务持久化仓库，默认保存任务在内存中，也可将任务保存在各种数据库中，任务中的数据序列化后保存到持久化数据库，从数据库加载后又反序列化。
# 触发器(Trigger)：描述调度任务被触发的条件。不过触发器完全是无状态的。
# 执行器(Executor)：负责处理作业的运行，它们通常通过在作业中提交指定的可调用对象到一个线程或者进程池来进行。当作业完成时，执行器将会通知调度器。

class MyCronTrigger(CronTrigger):
    """
    重写Cron定时
    """

    @classmethod
    def from_crontab(cls, expr, timezone=None):
        """
        0: second
        1: minute
        2: hour
        3: ?: day = None | W: 查找最近的工作日 | L -> last
        4: month
        5: L: day = last | ?/L: week = None | #: 转为整数 | week | #: day_of_week = 转为整数-1 | day_of_week = None
        6: year (optional)

        0 * * * * ?：每分钟执行一次
        0 0 3 * * ?：每天3点执行一次
        """
        values = expr.split()
        if len(values) != 6 and len(values) != 7:
            raise ValueError('Wrong number of fields; got {}, expected 6 or 7'.format(len(values)))

        second = values[0]
        minute = values[1]
        hour = values[2]
        if '?' in values[3]:
            day = None
        elif 'L' in values[5]:
            day = f"last {values[5].replace('L', '')}"
        elif 'W' in values[3]:
            day = cls.__find_recent_workday(int(values[3].split('W')[0]))
        else:
            day = values[3].replace('L', 'last')
        month = values[4]
        if '?' in values[5] or 'L' in values[5]:
            week = None
        elif '#' in values[5]:
            week = int(values[5].split('#')[1])
        else:
            week = values[5]
        if '#' in values[5]:
            day_of_week = int(values[5].split('#')[0]) - 1
        else:
            day_of_week = None
        year = values[6] if len(values) == 7 else None
        # 在类方法中，第一个参数通常命名为 cls，它代表调用该类方法的类本身
        # 使用 cls 可以访问类的属性和方法，并可以用于实例化类；调用 cls(...) 时，实际上是在创建当前类的一个新实例
        # 传递给 cls 的参数会传递给当前类的构造函数 __init__，如果当前类没有定义 __init__ 方法，Python 会自动调用父类的 __init__ 方法
        return cls(second=second, minute=minute, hour=hour, day=day, month=month, week=week,
                   day_of_week=day_of_week, year=year, timezone=timezone)

    @classmethod
    def __find_recent_workday(cls, day):
        now = datetime.now()
        date = datetime(now.year, now.month, day)
        if date.weekday() < 5:  # 工作日
            return date.day
        else:
            diff = 1
            while True:  # 如果不是工作日，则向前推一天，直到找到最近的工作日
                previous_day = date - timedelta(days=diff)
                if previous_day.weekday() < 5:
                    return previous_day.day
                else:
                    diff += 1


job_stores = {
    'default': MemoryJobStore(),  # 将任务存储在内存中，适合于短期任务或开发调试时使用
    # 将任务存储在一个支持 SQLAlchemy 的数据库中（如 MySQL、PostgreSQL），适合于持久化存储任务
    'sqlalchemy': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URL, engine=engine),
    'redis': RedisJobStore(  # 将任务存储在 Redis 数据库中，适合分布式系统中使用
        **dict(
            host=RedisConfig.redis_host,
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database
        )
    )
}
executors = {
    'default': ThreadPoolExecutor(20),  # 使用线程池来执行任务
    'processpool': ProcessPoolExecutor(5)  # 使用进程池来执行任务
}
job_defaults = {
    'coalesce': False,  # 如果在任务调度周期内错过了一个或多个任务运行时间，是否只运行一次（合并）。False 表示不合并，错过的任务将按计划依次执行
    'max_instance': 1  # 同一任务的最大并发实例数。1 表示同一时间只允许一个实例运行
}
scheduler = BackgroundScheduler()  # 调度器在后台线程中运行，不会阻塞当前线程
scheduler.configure(jobstores=job_stores, executors=executors, job_defaults=job_defaults)


class SchedulerUtil:
    """
    定时任务相关方法
    """

    @classmethod
    async def init_system_scheduler(cls, query_db: Session = SessionLocal()):
        """
        应用启动时初始化定时任务
        """
        logger.info("开始启动定时任务...")
        scheduler.start()
        job_list = JobDao.get_job_list_for_scheduler(query_db)
        for item in job_list:
            query_job = cls.get_scheduler_job(job_id=str(item.job_id))
            if query_job:
                cls.remove_scheduler_job(job_id=str(item.job_id))
            cls.add_scheduler_job(item)
        query_db.close()
        scheduler.add_listener(cls.scheduler_event_listener, EVENT_ALL)  # 为调度器添加一个事件监听器，用于监听调度器中的所有事件
        logger.info("系统初始定时任务加载成功")

    @classmethod
    async def close_system_scheduler(cls):
        """
        应用关闭时关闭定时任务
        """
        scheduler.shutdown()
        logger.info("关闭定时任务成功")

    @classmethod
    def get_scheduler_job(cls, job_id):
        """
        根据任务id获取任务对象
        :param job_id: 任务id
        :return: 任务对象
        """
        # APScheduler 提供了管理和查询任务的功能。APScheduler 维护一个任务调度器对象（如 BackgroundScheduler），该对象能够管理所有已调度的任务，包括添加、修改、删除和查询任务
        query_job = scheduler.get_job(job_id=str(job_id))

        return query_job

    @staticmethod
    def _resolve_callable(invoke_target: str):
        """
        将字符串形式的调用目标解析为可调用对象，避免使用 eval
        格式示例：module_task.video_cleanup.job
        """
        if not invoke_target or "." not in invoke_target:
            raise ValueError(f"无效的invoke_target: {invoke_target}")
        module_path, func_name = invoke_target.rsplit(".", 1)
        module = import_module(module_path)
        func = getattr(module, func_name, None)
        if func is None:
            raise AttributeError(f"在模块 {module_path} 中未找到函数 {func_name}")
        return func

    @classmethod
    def add_scheduler_job(cls, job_info):
        """
        根据输入的任务对象信息添加任务
        :param job_info: 任务对象信息
        """
        func = cls._resolve_callable(job_info.invoke_target)
        job_args = job_info.job_args.split(',') if job_info.job_args else None
        job_kwargs = loads(job_info.job_kwargs) if job_info.job_kwargs else None
        scheduler.add_job(
            func=func,  # 任务在调度时实际执行的函数
            trigger=MyCronTrigger.from_crontab(job_info.cron_expression),  # crontab
            args=job_args,  # 任务函数的位置参数
            kwargs=job_kwargs,  # 任务函数的关键字参数
            id=str(job_info.job_id),  # 任务的唯一标识符
            name=job_info.job_name,  # 任务的名称
            # 设置一个极大的失火宽限时间（使得任务不会因错过调度时间而被丢弃）
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            coalesce=True if job_info.misfire_policy == '2' else False,  # 设置任务合并，即如果任务因错过调度时间而积压，只运行一次；否则，运行每个错过的任务实例
            max_instances=3 if job_info.concurrent == '0' else 1,  # 允许最多 3 个并发实例；否则，只允许一个实例
            jobstore=job_info.job_group,  # 指定任务存储的位置
            executor=job_info.job_executor  # 指定执行任务的执行器
        )

    @classmethod
    def execute_scheduler_job_once(cls, job_info):
        """
        根据输入的任务对象执行一次任务
        :param job_info: 任务对象信息
        :return:
        """
        func = cls._resolve_callable(job_info.invoke_target)
        job_args = job_info.job_args.split(',') if job_info.job_args else None
        job_kwargs = loads(job_info.job_kwargs) if job_info.job_kwargs else None
        scheduler.add_job(
            func=func,
            # 向调度器添加任务。这个任务可以是周期性的（通过 cron 或 interval 触发器），也可以是一次性的（通过 date 触发器）
            trigger='date',  # 这是一个一次性任务
            run_date=datetime.now() + timedelta(seconds=1),  # 设置任务的运行时间为当前时间之后的一秒
            args=job_args,
            kwargs=job_kwargs,  # Deserialize
            id=str(job_info.job_id),
            name=job_info.job_name,
            misfire_grace_time=1000000000000 if job_info.misfire_policy == '3' else None,
            coalesce=True if job_info.misfire_policy == '2' else False,
            max_instances=3 if job_info.concurrent == '0' else 1,
            jobstore=job_info.job_group,
            executor=job_info.job_executor
        )

    @classmethod
    def remove_scheduler_job(cls, job_id):
        """
        根据任务id移除任务
        :param job_id: 任务id
        """
        scheduler.remove_job(job_id=str(job_id))

    @classmethod
    def scheduler_event_listener(cls, event):
        # 获取事件类型和任务ID
        event_type = event.__class__.__name__
        # 获取任务执行异常信息
        status = '0'
        exception_info = ''
        if event_type == 'JobExecutionEvent' and event.exception:
            exception_info = str(event.exception)
            status = '1'
        job_id = event.job_id
        query_job = cls.get_scheduler_job(job_id=job_id)
        if query_job:
            query_job_info = query_job.__getstate__()
            # 获取任务名称
            job_name = query_job_info.get('name')
            # 获取任务组名
            # _jobstore_alias 用于存储任务所在的任务存储（job store）的别名。这是任务在被添加到调度器时由调度器内部设置的。
            # 确保准确获取任务的存储位置，而不依赖于状态字典中是否包含相关信息
            job_group = query_job._jobstore_alias
            # 获取任务执行器
            job_executor = query_job_info.get('executor')
            # 获取调用目标字符串
            invoke_target = query_job_info.get('func')
            # 获取调用函数位置参数
            job_args = ','.join(query_job_info.get('args'))
            # 获取调用函数关键字参数 Serialize
            job_kwargs = dumps(query_job_info.get('kwargs'))
            # 获取任务触发器
            job_trigger = str(query_job_info.get('trigger'))
            # 构造日志消息
            job_message = f"事件类型: {event_type}, 任务ID: {job_id}, 任务名称: {job_name}, 执行于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            job_log = JobLogModel(
                jobName=job_name,
                jobGroup=job_group,
                jobExecutor=job_executor,
                invokeTarget=invoke_target,
                jobArgs=job_args,
                jobKwargs=job_kwargs,
                jobTrigger=job_trigger,
                jobMessage=job_message,
                status=status,
                exceptionInfo=exception_info
            )
            session = SessionLocal()
            JobLogService.add_job_log_services(session, job_log)  # 记录日志到数据库
            session.close()
