from redis import asyncio as aioredis
from utils.log_util import logger
from config.env import RedisConfig
from config.database import SessionLocal
from redis.exceptions import AuthenticationError, TimeoutError, RedisError
from module_admin.service.dict_service import DictDataService
from module_admin.service.config_service import ConfigService


class RedisUtil:
    """
    Redis相关类方法，可以在不需要创建类的实例的情况下调用。
    """
    @classmethod
    async def create_redis_pool(cls) -> aioredis.Redis:
        """
        应用启动时初始化redis连接
        :return: Redis连接对象
        """
        logger.info("开始连接redis...")
        redis = await aioredis.from_url(
            url=f"redis://{RedisConfig.redis_host}",
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username,
            password=RedisConfig.redis_password,
            db=RedisConfig.redis_database,
            encoding="utf-8",
            decode_responses=True
        )
        try:
            connection = await redis.ping()
            if connection:
                logger.info("redis连接成功")
            else:
                logger.error("redis连接失败")
        except AuthenticationError as e:
            logger.error(f"redis用户名或密码错误，详细错误信息：{e}")
        except TimeoutError as e:
            logger.error(f"redis连接超时，详细错误信息：{e}")
        except RedisError as e:
            logger.error(f"redis连接错误，详细错误信息：{e}")
        return redis

    @classmethod
    async def close_redis_pool(cls, app):
        """
        应用关闭时关闭redis连接
        :param app: fastapi对象
        """
        await app.state.redis.close()
        logger.info("关闭redis连接成功")

    @classmethod
    async def init_sys_dict(cls, redis):
        """
        应用启动时缓存字典表
        :param redis: redis对象
        """
        session = SessionLocal()
        await DictDataService.init_cache_sys_dict_services(session, redis)

        session.close()

    @classmethod
    async def init_sys_config(cls, redis):
        """
        应用启动时缓存参数配置表
        :param redis: redis对象
        :return:
        """
        session = SessionLocal()
        await ConfigService.init_cache_sys_config_services(session, redis)

        session.close()
