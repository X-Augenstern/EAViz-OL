from fastapi import APIRouter
from module_admin.service.login_service import *
from module_admin.entity.vo.login_vo import *
from module_admin.dao.login_dao import *
from module_admin.annotation.log_annotation import log_decorator
from config.env import JwtConfig, RedisInitKeyConfig
from utils.response_util import ResponseUtil
from utils.log_util import *
from datetime import timedelta

loginController = APIRouter()


@loginController.post("/login", response_model=Token)
@log_decorator(title='用户登录', business_type=0, log_type='login')
async def login(request: Request, form_data: CustomOAuth2PasswordRequestForm = Depends(),
                query_db: Session = Depends(get_db)):
    """
    1、根据用户名密码校验用户登录

    2、根据登录信息创建当前用户token（使用JWT编码）并添加到redis控制能否同时登录

    3、更新登录时间

    # 当 Depends() 是空的时，FastAPI 的行为如下：
    # 自动推断依赖项：FastAPI 会查看参数的类型注解，并尝试从中推断出依赖项。
    # 例如，form_data 的类型被注解为 CustomOAuth2PasswordRequestForm，因此 FastAPI 知道它需要实例化一个 CustomOAuth2PasswordRequestForm 对象。
    # 它需要在调用 login 函数之前被注入。FastAPI 会自动处理这个依赖项并将其实例化后传递给 login 函数

    在 FastAPI 中，直接实例化依赖项（如 form_data: CustomOAuth2PasswordRequestForm = CustomOAuth2PasswordRequestForm()）是不推荐的，

    因为这会导致以下问题：

    1、请求上下文问题：依赖项如 CustomOAuth2PasswordRequestForm 通常与请求上下文相关联，需要访问请求数据（如请求体、查询参数、头部等）。
    直接实例化它们会绕过 FastAPI 的请求上下文管理，导致无法正确处理请求数据。

    2、生命周期管理：FastAPI 使用依赖注入来管理依赖项的生命周期，包括创建、清理和处理依赖项的范围。
    直接实例化依赖项会跳过这些管理步骤，可能导致资源泄漏或不正确的依赖项管理。

    3、简洁性和可维护性：依赖注入模式使代码更简洁和模块化，易于测试和维护。使用 Depends() 明确表示这是一个依赖项，使代码更易读和理解。
    """
    captcha_enabled = True if await request.app.state.redis.get(
        f"{RedisInitKeyConfig.SYS_CONFIG.get('key')}:sys.account.captchaEnabled") == 'true' else False
    user = UserLogin(
        userName=form_data.username,
        password=form_data.password,
        code=form_data.code,
        uuid=form_data.uuid,
        loginInfo=form_data.login_info,
        captchaEnabled=captcha_enabled
    )
    try:
        result = await LoginService.authenticate_user(request, query_db, user)
    except LoginException as e:
        return ResponseUtil.failure(msg=e.message)

    try:
        access_token_expires = timedelta(minutes=JwtConfig.jwt_expire_minutes)
        session_id = str(uuid4())
        access_token = LoginService.create_access_token(
            data={
                "user_id": str(result[0].user_id),
                "user_name": result[0].user_name,
                "dept_name": result[1].dept_name if result[1] else None,
                "session_id": session_id,
                "login_info": user.login_info
            },
            expires_delta=access_token_expires
        )

        if AppConfig.app_same_time_login:
            await request.app.state.redis.set(f"{RedisInitKeyConfig.ACCESS_TOKEN.get('key')}:{session_id}",
                                              access_token,
                                              ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes))
        else:
            # 此方法可实现同一账号同一时间只能登录一次
            await request.app.state.redis.set(f"{RedisInitKeyConfig.ACCESS_TOKEN.get('key')}:{result[0].user_id}",
                                              access_token,
                                              ex=timedelta(minutes=JwtConfig.jwt_redis_expire_minutes))

        UserService.edit_user_services(query_db,
                                       EditUserModel(userId=result[0].user_id, loginDate=datetime.now(), type='status'))
        logger.info('登录成功')

        # 判断请求是否来自于api文档，如果是返回指定格式的结果，用于修复api文档认证成功后token显示undefined的bug
        request_from_swagger = request.headers.get('referer').endswith('docs') if request.headers.get(
            'referer') else False
        request_from_redoc = request.headers.get('referer').endswith('redoc') if request.headers.get(
            'referer') else False
        if request_from_swagger or request_from_redoc:
            return {'access_token': access_token, 'token_type': 'Bearer'}

        return ResponseUtil.success(
            msg='登录成功',
            dict_content={'token': access_token}
        )
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@loginController.get("/getInfo", response_model=CurrentUserModel)
async def get_login_user_info(request: Request,
                              current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    根据token获取当前用户信息
    """
    try:
        logger.info('获取成功')
        return ResponseUtil.success(model_content=current_user)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@loginController.get("/getRouters")
async def get_login_user_routers(request: Request,
                                 current_user: CurrentUserModel = Depends(LoginService.get_current_user),
                                 query_db: Session = Depends(get_db)):
    """
    根据用户id获取当前用户路由信息
    """
    try:
        logger.info('获取成功')
        user_routers = await LoginService.get_current_user_routers(current_user.user.user_id, query_db)
        return ResponseUtil.success(data=user_routers)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@loginController.post("/register", response_model=CrudResponseModel)
async def register_user(request: Request, user_register: UserRegister, query_db: Session = Depends(get_db)):
    """
    用户注册
    """
    try:
        user_register_result = await LoginService.register_user_services(request, query_db, user_register)
        if user_register_result.is_success:
            logger.info(user_register_result.message)
            return ResponseUtil.success(data=user_register_result, msg=user_register_result.message)
        else:
            logger.warning(user_register_result.message)
            return ResponseUtil.failure(msg=user_register_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


# @loginController.post("/getSmsCode", response_model=SmsCode)
# async def get_sms_code(request: Request, user: ResetUserModel, query_db: Session = Depends(get_db)):
#     try:
#         sms_result = await LoginService.get_sms_code_services(request, query_db, user)
#         if sms_result.is_success:
#             logger.info('获取成功')
#             return ResponseUtil.success(data=sms_result)
#         else:
#             logger.warning(sms_result.message)
#             return ResponseUtil.failure(msg=sms_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))
#
#
# @loginController.post("/forgetPwd", response_model=CrudResponseModel)
# async def forget_user_pwd(request: Request, forget_user: ResetUserModel, query_db: Session = Depends(get_db)):
#     try:
#         forget_user_result = await LoginService.forget_user_services(request, query_db, forget_user)
#         if forget_user_result.is_success:
#             logger.info(forget_user_result.message)
#             return ResponseUtil.success(data=forget_user_result, msg=forget_user_result.message)
#         else:
#             logger.warning(forget_user_result.message)
#             return ResponseUtil.failure(msg=forget_user_result.message)
#     except Exception as e:
#         logger.exception(e)
#         return ResponseUtil.error(msg=str(e))


@loginController.post("/logout")
async def logout(request: Request, token: Optional[str] = Depends(oauth2_scheme)):
    """
    退出登录
    """
    try:
        # 通常情况下，JWT 会包含一个 exp 声明，表示令牌的过期时间。在解码 JWT 时，默认情况下库会验证这个时间，如果令牌已过期就会抛出异常。
        # 但是在某些情况下可能希望解码一个已经过期的令牌以读取其中的数据，这时可以使用 options={'verify_exp': False} 来跳过过期验证。
        # 即使 token 已经过期，jwt.decode 函数也会成功解码并返回令牌中的数据，而不会因为令牌过期而报错。
        payload = jwt.decode(token, JwtConfig.jwt_secret_key, algorithms=[JwtConfig.jwt_algorithm],
                             options={'verify_exp': False})
        session_id: str = payload.get("session_id")
        await LoginService.logout_services(request, session_id)
        logger.info('退出成功')
        return ResponseUtil.success(msg="退出成功")
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
