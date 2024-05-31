from fastapi import Request
from module_admin.entity.vo.cache_vo import *
from config.env import RedisInitKeyConfig
from config.get_redis import RedisUtil
from module_admin.entity.vo.common_vo import CrudResponseModel


class CacheService:
    """
    缓存监控模块服务层
    """
    @classmethod
    async def get_cache_monitor_statistical_info_services(cls, request: Request):
        """
        获取缓存监控信息service
        :param request: Request对象
        :return: 缓存监控信息
        """
        info = await request.app.state.redis.info()  # 返回包含 Redis 服务器信息和统计数据的字典
        db_size = await request.app.state.redis.dbsize()  # 返回当前数据库的键数量
        command_stats_dict = await request.app.state.redis.info('commandstats')  # 返回一个字典，包含各个命令的统计信息
        # eg:{
        #        "cmdstat_get": {
        #            "calls": 5000,
        #            "usec": 20000,
        #            "usec_per_call": 4.0
        #        },
        #        "cmdstat_set": {
        #            "calls": 3000,
        #            "usec": 15000,
        #            "usec_per_call": 5.0
        #        }
        #        // 其他命令统计
        #    }
        # -> [{"name":"get","value":"5000"},{"name":"set","value":"3000"}]
        command_stats = [dict(name=key.split('_')[1], value=str(value.get('calls'))) for key, value in
                         command_stats_dict.items()]
        result = CacheMonitorModel(
            commandStats=command_stats,
            dbSize=db_size,
            info=info
        )

        return result

    @classmethod
    def get_cache_monitor_cache_name_services(cls):
        """
        获取缓存名称列表信息service
        :return: 缓存名称列表信息
        """
        name_list = []
        # dir：返回一个由字符串组成的列表，这些字符串是对象中可用的属性和方法的名称，输出中还包括一些 Python 内置的特殊方法和属性（以双下划线开头和结尾）
        # ACCESS_TOKEN
        # ACCOUNT_LOCK
        # CAPTCHA_CODES
        # PASSWORD_ERROR_COUNT
        # SMS_CODE
        # SYS_CONFIG
        # SYS_DICT
        # __class__
        # __delattr__
        # __dict__
        # __dir__
        # __doc__
        # __eq__
        # __format__
        # __ge__
        # __getattribute__
        # __gt__
        # __hash__
        # __init__
        # __init_subclass__
        # __le__
        # __lt__
        # __module__
        # __ne__
        # __new__
        # __reduce__
        # __reduce_ex__
        # __repr__
        # __setattr__
        # __sizeof__
        # __str__
        # __subclasshook__
        # __weakref__
        for attr_name in dir(RedisInitKeyConfig):
            if not attr_name.startswith('__') and isinstance(getattr(RedisInitKeyConfig, attr_name), dict):
                name_list.append(
                    CacheInfoModel(
                        cacheKey="",
                        cacheName=getattr(RedisInitKeyConfig, attr_name).get('key'),
                        cacheValue="",
                        remark=getattr(RedisInitKeyConfig, attr_name).get('remark')
                    )
                )

        return name_list

    @classmethod
    async def get_cache_monitor_cache_key_services(cls, request: Request, cache_name: str):
        """
        获取缓存键名列表信息service
        :param request: Request对象
        :param cache_name: 缓存名称
        :return: 缓存键名列表信息
        """
        cache_keys = await request.app.state.redis.keys(f"{cache_name}*")
        # key.split(':', 1): 这个方法将字符串 key 按照冒号 : 进行分隔，并且最多分隔一次。split 方法的第一个参数是分隔符，第二个参数是分隔次数
        cache_key_list = [key.split(':', 1)[1] for key in cache_keys if key.startswith(f"{cache_name}:")]

        # cache_name = 'sys_dict' -> ['sys_common_status','sys_job_executor',...]
        return cache_key_list

    @classmethod
    async def get_cache_monitor_cache_value_services(cls, request: Request, cache_name: str, cache_key: str):
        """
        获取缓存内容信息service
        :param request: Request对象
        :param cache_name: 缓存名称
        :param cache_key: 缓存键名
        :return: 缓存内容信息
        """
        cache_value = await request.app.state.redis.get(f"{cache_name}:{cache_key}")

        # [{"dictCode": 15, "dictSort": 1, "dictLabel": "是", "dictValue": "Y", "dictType": "sys_yes_no",
        # "cssClass": "", "listClass": "primary", "isDefault": "Y", "status": "0", "createBy": "admin",
        # "createTime": "2024-05-05 17:10:15", "updateBy": "", "updateTime": null, "remark": "系统默认是"},
        # {"dictCode": 16, "dictSort": 2, "dictLabel": "否", "dictValue": "N", "dictType": "sys_yes_no",
        # "cssClass": "", "listClass": "danger", "isDefault": "N", "status": "0", "createBy": "admin",
        # "createTime": "2024-05-05 17:10:15", "updateBy": "", "updateTime": null, "remark": "系统默认否"}]

        return CacheInfoModel(cacheKey=cache_key, cacheName=cache_name, cacheValue=cache_value, remark="")

    @classmethod
    async def clear_cache_monitor_cache_name_services(cls, request: Request, cache_name: str):
        """
        清除缓存名称对应所有键值（用cache_name*去匹配）service
        :param request: Request对象
        :param cache_name: 缓存名称
        :return: 操作缓存响应信息
        """
        cache_keys = await request.app.state.redis.keys(f"{cache_name}*")
        if cache_keys:
            await request.app.state.redis.delete(*cache_keys)
        result = dict(is_success=True, message=f"{cache_name}对应键值清除成功")

        return CrudResponseModel(**result)

    @classmethod
    async def clear_cache_monitor_cache_key_services(cls, request: Request, cache_key: str):
        """
        清除缓存键名对应所有键值（用*cache_key去匹配）service
        :param request: Request对象
        :param cache_key: 缓存键名
        :return: 操作缓存响应信息
        """
        cache_keys = await request.app.state.redis.keys(f"*{cache_key}")
        if cache_keys:
            await request.app.state.redis.delete(*cache_keys)
        result = dict(is_success=True, message=f"{cache_key}清除成功")

        return CrudResponseModel(**result)

    @classmethod
    async def clear_cache_monitor_all_services(cls, request: Request):
        """
        清除所有缓存（从数据库中重新加载）service
        :param request: Request对象
        :return: 操作缓存响应信息
        """
        cache_keys = await request.app.state.redis.keys()
        if cache_keys:
            # * 用于将列表（或可迭代对象）的元素解构（拆包）到函数参数或者将一个列表解构成多个变量
            # 1、将cache_keys中的元素作为参数一起传递给delete(ele1,ele2,...)
            # 2、eg：a, *b, c = cache_keys： a 取得列表的第一个元素，c 取得列表的最后一个元素，而 b 则取得中间的所有元素作为一个列表

            # ** 用于将字典的键值对解构（拆包）到函数参数或者将多个字典合并
            # 1、person = {'name': 'Alice', 'age': 30}
            # **person 会将字典 person 中的键值对 name='Alice' 和 age=30 分别作为参数传递给 greet(name, age)
            # 2、dict1 = {'a': 1, 'b': 2} dict2 = {'b': 3, 'c': 4}
            # merged_dict = {**dict1, **dict2} {'a': 1, 'b': 3, 'c': 4} 如果有重复的键，后面的字典中的值会覆盖前面的

            # * 用于解构列表（或其他可迭代对象），可以在函数调用时拆开列表传参，或在赋值时将列表拆分成多个变量
            # ** 用于解构字典，可以在函数调用时拆开字典传参，或将多个字典合并成一个新的字典
            await request.app.state.redis.delete(*cache_keys)

        result = dict(is_success=True, message="所有缓存清除成功")
        await RedisUtil.init_sys_dict(request.app.state.redis)
        await RedisUtil.init_sys_config(request.app.state.redis)

        return CrudResponseModel(**result)
