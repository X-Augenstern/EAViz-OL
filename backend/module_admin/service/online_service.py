from fastapi import Request
from jose import jwt
from config.env import JwtConfig, RedisInitKeyConfig
from module_admin.entity.vo.online_vo import *
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.common_util import CamelCaseUtil


class OnlineService:
    """
    在线用户管理模块服务层
    """
    @classmethod
    async def get_online_list_services(cls, request: Request, query_object: OnlineQueryModel):
        """
        从redis获取在线用户表信息（使用JWT解码）service
        :param request: Request对象
        :param query_object: 查询参数对象
        :return: 在线用户列表信息
        """
        access_token_keys = await request.app.state.redis.keys(f"{RedisInitKeyConfig.ACCESS_TOKEN.get('key')}*")
        if not access_token_keys:
            access_token_keys = []
        access_token_values_list = [await request.app.state.redis.get(key) for key in access_token_keys]
        online_info_list = []
        for item in access_token_values_list:
            # 使用 JWT（JSON Web Token）库解码一个 JWT 令牌，并提取其有效载荷部分
            # item 是需要解码的 JWT 令牌，它是从 Redis 中获取的 access_token 值
            # JwtConfig.jwt_secret_key 是解码 JWT 所需的秘密密钥。JWT 使用这个密钥来验证令牌的签名，以确保令牌的真实性和完整性

            # 解码过程：
            # 1、JWT 是由三部分组成的字符串：头部（header）、载荷（payload）、签名（signature），通常用点 . 分隔开
            # 2、jwt.decode 函数使用提供的密钥和算法验证令牌的签名，以确保令牌未被篡改
            # 3、如果签名验证成功，函数会解码 JWT 并返回其中的有效载荷部分，通常是一个包含用户信息的字典（payload） -> dict
            payload = jwt.decode(item, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm])
            online_dict = dict(
                token_id=payload.get('session_id'),
                user_name=payload.get('user_name'),
                dept_name=payload.get('dept_name'),
                ipaddr=payload.get('login_info').get('ipaddr'),
                login_location=payload.get('login_info').get('loginLocation'),
                browser=payload.get('login_info').get('browser'),
                os=payload.get('login_info').get('os'),
                login_time=payload.get('login_info').get('loginTime')
            )
            if query_object.user_name and not query_object.ipaddr:
                if query_object.user_name == payload.get('user_name'):
                    online_info_list = [online_dict]
                    break
            elif not query_object.user_name and query_object.ipaddr:
                if query_object.ipaddr == payload.get('login_info').get('ipaddr'):
                    online_info_list = [online_dict]
                    break
            elif query_object.user_name and query_object.ipaddr:
                if query_object.user_name == payload.get('user_name') and query_object.ipaddr == payload.get(
                        'login_info').get('ipaddr'):
                    online_info_list = [online_dict]
                    break
            else:  # 没有查询条件则获取全部
                online_info_list.append(online_dict)

        return CamelCaseUtil.transform_result(online_info_list)

    @classmethod
    async def delete_online_services(cls, request: Request, page_object: DeleteOnlineModel):
        """
        强退在线用户信息（删除redis中相应的键值）service
        :param request: Request对象
        :param page_object: 强退在线用户对象
        :return: 强退在线用户校验结果
        """
        if page_object.token_ids:
            token_id_list = page_object.token_ids.split(',')
            for token_id in token_id_list:
                await request.app.state.redis.delete(f"{RedisInitKeyConfig.ACCESS_TOKEN.get('key')}:{token_id}")
            result = dict(is_success=True, message='强退成功')
        else:
            result = dict(is_success=False, message='传入session_id为空')
        return CrudResponseModel(**result)
