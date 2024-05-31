from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from exceptions.exception import AuthException, PermissionException
from utils.response_util import ResponseUtil, JSONResponse, jsonable_encoder


def handle_exception(app: FastAPI):
    """
    全局异常处理：这些处理器用于捕获和处理特定类型的异常，并返回适当的响应给客户端。

    e. g.:当在代码中抛出 AuthException 异常时，FastAPI 会捕获这个异常，并使用定义的 auth_exception_handler 异常处理器，返回相应的响应。
    """
    # 自定义token检验异常
    @app.exception_handler(AuthException)
    async def auth_exception_handler(request: Request, exc: AuthException):
        """
        当发生 AuthException 异常时，这个处理器将被调用。处理器返回一个未授权的响应，包含异常数据和消息。
        """
        return ResponseUtil.unauthorized(data=exc.data, msg=exc.message)

    # 自定义权限检验异常
    @app.exception_handler(PermissionException)
    async def permission_exception_handler(request: Request, exc: PermissionException):
        """
        当发生 PermissionException 异常时，这个处理器将被调用。处理器返回一个禁止访问的响应，包含异常数据和消息。
        """
        return ResponseUtil.forbidden(data=exc.data, msg=exc.message)

    # 处理其他http请求异常
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        当发生 HTTPException 异常时，这个处理器将被调用。HTTPException 是一个通用的异常类型，通常用于处理 HTTP 请求错误，如 404 未找到或 500 服务器错误。
        处理器返回一个 JSON 响应，包含异常的状态码和详细信息。
        """
        return JSONResponse(
            content=jsonable_encoder({"code": exc.status_code, "msg": exc.detail}),
            status_code=exc.status_code
        )
