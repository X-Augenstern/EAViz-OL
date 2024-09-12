from functools import wraps, lru_cache
from fastapi import Request
from fastapi.responses import JSONResponse, ORJSONResponse, UJSONResponse
from inspect import getfile
from os import path, getcwd
from json import loads, dumps
from time import time
from datetime import datetime
from requests import get
from user_agents import parse
from typing import Optional
from module_admin.service.login_service import LoginService
from module_admin.service.log_service import OperationLogService, LoginLogService
from module_admin.entity.vo.log_vo import OperLogModel, LogininforModel
from config.env import AppConfig


def log_decorator(title: str, business_type: int, log_type: Optional[str] = 'operation'):
    """
    日志装饰器

    预处理：

    1、记录开始时间：记录函数调用开始的时间点，用于后续计算函数执行耗时。

    2、路径和函数信息：获取被装饰函数的文件路径、项目根目录、相对路径，并生成一个详细的函数调用路径字符串。

    3、请求和上下文信息获取：
        从kwargs中提取request和数据库查询对象query_db。
        获取请求方法（如GET、POST）和请求头中的User-Agent来判断操作系统和设备类型。
        根据请求IP地址获取地理位置信息。
        根据内容类型，从请求中提取表单数据或JSON数据，并将其转换为字符串或字典形式，用于记录操作参数。

    4、登录信息处理：如果日志类型是登录日志，解析User-Agent来获取浏览器和操作系统信息，并创建登录日志字典。

    调用被修饰函数

    1、执行被装饰函数：将上下文信息（如请求数据和登录日志）传递给被装饰函数，并异步执行该函数。

    后处理：

    1、计算执行耗时：计算从开始到现在的时间差，作为函数执行耗时。

    2、获取响应数据：根据被装饰函数的返回类型（如JSONResponse等），提取响应体中的数据。

    3、分析响应结果：根据响应数据确定操作的成功或失败状态，并记录错误信息。

    4、日志记录：
        如果是登录日志，根据是否是API文档请求决定是否记录日志，并将登录信息插入登录日志表。
        否则，获取当前用户信息，创建操作日志，并记录到操作日志表中。

    5、返回结果：返回被装饰函数的执行结果。

    :param log_type: 日志类型（login表示登录日志，为空表示为操作日志）
    :param title: 当前日志装饰器装饰的模块标题
    :param business_type: 业务类型（0其它 1新增 2修改 3删除 4授权 5导出 6导入 7强退 8生成代码 9清空数据 10获取EDF数据
                                  11分析ESCSD 12分析AD 13分析SpiD 14分析SRD 15分析VD）
    """

    def decorator(func):  # 装饰器函数 decorator，接收一个函数 func
        @wraps(func)
        async def wrapper(*args, **kwargs):  # 包装函数 wrapper，使用 @wraps 保留原始函数的元数据、名称和文档字符串
            """
            def log_decorator(title: str, business_type: int, log_type: Optional[str] = 'operation'):
                def decorator(func):  # 装饰器函数 decorator，接收一个函数 func
                    @wraps(func)
                    async def wrapper(*args, **kwargs):  # 包装函数 wrapper，使用 @wraps 保留原始函数的元数据
                        # 预处理逻辑
                        # 调用被装饰函数
                        result = await func(*args, **kwargs)  # 异步调用被装饰函数并获取返回结果
                        # 后处理逻辑
                        return result  # 返回被装饰函数的结果
                    return wrapper  # 返回包装函数
                return decorator  # 返回装饰器函数
            
            调用流程解析：
            1、外层函数 (log_decorator)：
                用于接收装饰器参数 title、business_type、log_type。
                返回实际的装饰器函数 decorator。
            2、实际的装饰器函数 (decorator)：
                接收要被装饰的函数 func。
                返回包装函数 wrapper。
            3、包装函数 (wrapper)：
                执行预处理逻辑，如记录开始时间、获取路径和请求信息。
                异步调用被装饰的函数 func 并获取返回结果。
                执行后处理逻辑，如记录日志、计算耗时。
                返回被装饰函数的结果。
                
            在 Python 中，装饰器的定义和使用并不依赖于特定的函数名，而是依赖于装饰器的语法和返回值。具体来说：
            装饰器的定义：装饰器是一个函数，它接受另一个函数作为参数，并返回一个新的函数。
            装饰器的使用：通过使用 @装饰器名 语法，将装饰器应用于一个函数。
            log_decorator 定义了一个装饰器工厂函数，它返回实际的装饰器 decorator。然后，decorator 返回包装函数 wrapper。可以随意修改函数名，只要逻辑保持一致。
            """

            """
            *args 和 **kwargs 是用于接收不定数量参数的两种机制，它们非常适合用于装饰器中，因为装饰器通常需要处理被装饰函数的所有参数而不做修改。
            
            *args：用于接收任意数量的位置参数，作为一个元组传递给函数。
            **kwargs：用于接收任意数量的关键字参数，作为一个字典传递给函数。
            
            使用 *args 和 **kwargs 可以确保装饰器能处理被装饰函数的所有参数，而不需要预先知道这些参数的具体数量和名称。这在编写通用装饰器时特别有用，因为可能不知道被装饰的函数会接受哪些参数。
            
            def my_decorator(func):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    print(f"Arguments were: {args}, {kwargs}")
                    result = func(*args, **kwargs)
                    print(f"Result was: {result}")
                    return result
                return wrapper
            
            @my_decorator
            def example_function(a, b, c=3):
                return a + b + c
            
            # 调用被装饰的函数
            example_function(1, 2, c=4)
            
            ->  Arguments were: (1, 2), {'c': 4}
                Result was: 7
            
            ----
            
            结合普通参数和 *args, **kwargs，确保某些参数必须被提供，同时仍然允许接收额外的位置和关键字参数。
            def example_function(arg1, arg2, *args, **kwargs):
                print("arg1:", arg1)
                print("arg2:", arg2)
                print("Additional arguments:", args)
                print("Additional keyword arguments:", kwargs)
            
            example_function(1, 2, 3, 4, 5, key1='value1', key2='value2')
            
            ->  arg1: 1
                arg2: 2
                Additional arguments: (3, 4, 5)
                Additional keyword arguments: {'key1': 'value1', 'key2': 'value2'}
            """
            start_time = time()  # 记录函数开始执行的时间

            # eg: '/home/user/project/module/submodule/example.py'
            file_path = getfile(func)  # 获取被装饰函数的文件路径
            # eg: '/home/user/project'
            project_root = getcwd()  # 获取项目根路径
            # eg: 'module.submodule.example.' 获取文件相对于项目根路径的相对路径并去掉文件扩展名的最后两个字符（py）
            relative_path = path.relpath(file_path, start=project_root)[0:-2].replace('\\', '.')
            # eg: 'module.submodule.example.my_function()'
            func_path = f'{relative_path}{func.__name__}()'  # 获取当前被装饰函数所在路径

            # 获取上下文信息
            request: Request = kwargs.get('request')  # 从 kwargs（关键字参数）中获取名为 request 的对象，它应该是一个 Request 对象，包含了当前请求的所有信息
            query_db = kwargs.get('query_db')  # 从 kwargs 中获取名为 query_db 的对象，这通常是一个数据库连接对象，用于查询数据库
            request_method = request.method  # 获取请求的方法（HTTP 动词），例如 GET、POST 等
            operator_type = 0

            user_agent = request.headers.get('User-Agent')  # 从请求头中获取 User-Agent 字段的值，这个字段包含了有关客户端设备和浏览器的信息
            if "Windows" in user_agent or "Macintosh" in user_agent or "Linux" in user_agent:
                operator_type = 1  # 桌面设备
            if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
                operator_type = 2  # 移动设备

            oper_url = request.url.path  # 获取请求的url
            oper_ip = request.headers.get("X-Forwarded-For")  # 获取请求的ip及ip归属区域
            oper_location = '内网IP'
            if AppConfig.app_ip_location_query:
                oper_location = get_ip_location(oper_ip)

            # 根据不同的请求类型使用不同的方法获取请求参数
            content_type = request.headers.get("Content-Type")  # 从请求头中获取 Content-Type 字段的值，这个字段指明了请求体的媒体类型
            # 请求体包含表单数据
            if content_type and (
                    "multipart/form-data" in content_type or 'application/x-www-form-urlencoded' in content_type):
                payload = await request.form()  # 获取表单数据
                oper_param = "\n".join([f"{key}: {value}" for key, value in payload.items()])  # 将表单数据转换为字符串，每个键值对用换行符分隔
            else:
                payload = await request.body()  # 获取请求体数据
                path_params = request.path_params  # 获取请求路径参数
                oper_param = {}
                if payload:
                    oper_param.update(loads(str(payload, 'utf-8')))  # 如果请求体有数据，则将其解码为 JSON 并更新 oper_param 字典
                if path_params:
                    oper_param.update(path_params)  # # 如果有路径参数，则将其更新到 oper_param 字典中
                oper_param = dumps(oper_param, ensure_ascii=False)  # # 将 oper_param 字典转换为 JSON 字符串
            if len(oper_param) > 2000:  # 日志表请求参数字段长度最大为2000
                oper_param = '请求参数过长'

            # 如果日志类型是登录日志，获取浏览器和操作系统信息，并在登录之前传递一些登录信息
            oper_time = datetime.now()  # 获取操作时间
            login_log = {}
            if log_type == 'login':
                user_agent_info = parse(user_agent)  # 解析 User-Agent 字符串，提取出浏览器和操作系统信息
                browser = f'{user_agent_info.browser.family}'  # 获取浏览器的家族名称，例如 Chrome、Firefox 等
                system_os = f'{user_agent_info.os.family}'  # 获取操作系统的家族名称，例如 Windows、Mac OS、Linux 等
                if user_agent_info.browser.version != ():  # 浏览器版本信息如果存在
                    browser += f' {user_agent_info.browser.version[0]}'  # Chrome 91
                if user_agent_info.os.version != ():
                    system_os += f' {user_agent_info.os.version[0]}'  # Windows 10
                login_log = dict(
                    ipaddr=oper_ip,
                    loginLocation=oper_location,
                    browser=browser,
                    os=system_os,
                    loginTime=oper_time.strftime('%Y-%m-%d %H:%M:%S')
                )
                # 将 login_log 字典赋值给 kwargs 中的 form_data 对象的 login_info 属性。这允许被装饰的函数访问这些登录信息
                kwargs['form_data'].login_info = login_log

            # 调用被装饰的异步函数，并将之前所有预处理的上下文信息传递给它。在这行代码之前的所有操作都可以看作是装饰器给这个函数添加的预处理逻辑
            result = await func(*args, **kwargs)

            cost_time = float(time() - start_time) * 100  # 获取请求耗时

            # 判断请求是否来自api文档
            request_from_swagger = request.headers.get('referer').endswith('docs') if request.headers.get(
                'referer') else False
            request_from_redoc = request.headers.get('referer').endswith('redoc') if request.headers.get(
                'referer') else False
            # 根据响应结果的类型使用不同的方法获取响应结果参数
            if isinstance(result, JSONResponse) or isinstance(result, ORJSONResponse) or isinstance(result,
                                                                                                    UJSONResponse):
                result_dict = loads(str(result.body, 'utf-8'))
            else:
                if request_from_swagger or request_from_redoc:
                    result_dict = {}
                else:
                    if result.status_code == 200:
                        result_dict = {'code': result.status_code, 'message': '获取成功'}
                    else:
                        result_dict = {'code': result.status_code, 'message': '获取失败'}
            json_result = dumps(result_dict, ensure_ascii=False)

            # 根据响应结果获取响应状态及异常信息
            status = 1
            error_msg = ''
            if result_dict.get('code') == 200:
                status = 0
            else:
                error_msg = result_dict.get('msg')

            # 根据日志类型向对应的日志表插入数据
            if log_type == 'login':
                if request_from_swagger or request_from_redoc:  # 登录请求来自于api文档时不记录登录日志，其余情况则记录
                    pass
                else:
                    user = kwargs.get('form_data')
                    user_name = user.username
                    login_log['loginTime'] = oper_time
                    login_log['userName'] = user_name
                    login_log['status'] = str(status)
                    login_log['msg'] = result_dict.get('msg')

                    LoginLogService.add_login_log_services(query_db, LogininforModel(**login_log))
            else:
                token = request.headers.get('Authorization')  # 从请求头中获取 Authorization 字段的值，这通常是用于认证和授权的令牌
                current_user = await LoginService.get_current_user(request, token, query_db)
                oper_name = current_user.user.user_name
                dept_name = current_user.user.dept.dept_name if current_user.user.dept else None
                operation_log = OperLogModel(
                    title=title,
                    businessType=business_type,
                    method=func_path,
                    requestMethod=request_method,
                    operatorType=operator_type,
                    operName=oper_name,
                    deptName=dept_name,
                    operUrl=oper_url,
                    operIp=oper_ip,
                    operLocation=oper_location,
                    operParam=oper_param,
                    jsonResult=json_result,
                    status=status,
                    errorMsg=error_msg,
                    operTime=oper_time,
                    costTime=int(cost_time)
                )
                OperationLogService.add_operation_log_services(query_db, operation_log)

            return result

        return wrapper

    return decorator


@lru_cache()
def get_ip_location(oper_ip: str):
    """
    查询ip归属区域
    :param oper_ip: 需要查询的ip
    :return: ip归属区域
    """
    oper_location = '内网IP'
    try:
        if oper_ip != '127.0.0.1' and oper_ip != 'localhost':
            oper_location = '未知'
            ip_result = get(f'https://qifu-api.baidubce.com/ip/geo/v1/district?ip={oper_ip}')
            if ip_result.status_code == 200:
                prov = ip_result.json().get('data').get('prov')
                city = ip_result.json().get('data').get('city')
                if prov or city:
                    oper_location = f'{prov}-{city}'
    except Exception as e:
        oper_location = '未知'
        print(e)
    return oper_location
