from fastapi import status
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class ResponseUtil:
    """
    响应工具类
    """

    @classmethod
    def success(cls, msg: str = '操作成功', data: Optional[Any] = None, rows: Optional[Any] = None,
                dict_content: Optional[Dict] = None, model_content: Optional[BaseModel] = None) -> Response:
        """
        成功响应方法
        :param msg: 可选，自定义成功响应信息
        :param data: 可选，成功响应结果中属性为data的值
        :param rows: 可选，成功响应结果中属性为rows的值
        :param dict_content: 可选，dict类型，成功响应结果中自定义属性的值
        :param model_content: 可选，BaseModel类型，成功响应结果中自定义属性的值
        :return: 成功响应结果
        """
        result = {
            'code': 200,
            'msg': msg
        }

        if data is not None:
            result['data'] = data
        if rows is not None:
            result['rows'] = rows
        if dict_content is not None:
            # 使用update函数是因为dict_content是一个字典，可能包含多个键值对，而直接像data和rows那样赋值只能处理单个键值对
            # 使用update可以一次性将整个字典的内容合并到result字典中。这样不仅简洁，还能动态处理字典中的多个键值对：
            # dict_content = {'key1': 'value1', 'key2': 'value2'}
            # result.update(dict_content) —> result['key1'] = 'value1' result['key2'] = 'value2'
            # 如果用直接赋值的方法，则需要提前知道所有键的名称，并且无法动态处理：
            # result['key1'] = dict_content['key1']
            # result['key2'] = dict_content['key2']
            # 使用update方法不仅简洁，还能处理动态或不确定的字典内容
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        result.update({'success': True, 'time': datetime.now()})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )

    @classmethod
    def failure(cls, msg: str = '操作失败', data: Optional[Any] = None, rows: Optional[Any] = None,
                dict_content: Optional[Dict] = None, model_content: Optional[BaseModel] = None) -> Response:
        """
        失败响应方法
        :param msg: 可选，自定义失败响应信息
        :param data: 可选，失败响应结果中属性为data的值
        :param rows: 可选，失败响应结果中属性为rows的值
        :param dict_content: 可选，dict类型，失败响应结果中自定义属性的值
        :param model_content: 可选，BaseModel类型，失败响应结果中自定义属性的值
        :return: 失败响应结果
        """
        result = {
            'code': 601,
            'msg': msg
        }

        if data is not None:
            result['data'] = data
        if rows is not None:
            result['rows'] = rows
        if dict_content is not None:
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        result.update({'success': False, 'time': datetime.now()})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )

    @classmethod
    def unauthorized(cls, msg: str = '登录信息已过期，访问系统资源失败', data: Optional[Any] = None,
                     rows: Optional[Any] = None,
                     dict_content: Optional[Dict] = None, model_content: Optional[BaseModel] = None) -> Response:
        """
        未认证响应方法
        :param msg: 可选，自定义未认证响应信息
        :param data: 可选，未认证响应结果中属性为data的值
        :param rows: 可选，未认证响应结果中属性为rows的值
        :param dict_content: 可选，dict类型，未认证响应结果中自定义属性的值
        :param model_content: 可选，BaseModel类型，未认证响应结果中自定义属性的值
        :return: 未认证响应结果
        """
        result = {
            'code': 401,
            'msg': msg
        }

        if data is not None:
            result['data'] = data
        if rows is not None:
            result['rows'] = rows
        if dict_content is not None:
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        result.update({'success': False, 'time': datetime.now()})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )

    @classmethod
    def forbidden(cls, msg: str = '该用户无此接口权限', data: Optional[Any] = None, rows: Optional[Any] = None,
                  dict_content: Optional[Dict] = None, model_content: Optional[BaseModel] = None) -> Response:
        """
        未认证响应方法
        :param msg: 可选，自定义未认证响应信息
        :param data: 可选，未认证响应结果中属性为data的值
        :param rows: 可选，未认证响应结果中属性为rows的值
        :param dict_content: 可选，dict类型，未认证响应结果中自定义属性的值
        :param model_content: 可选，BaseModel类型，未认证响应结果中自定义属性的值
        :return: 未认证响应结果
        """
        result = {
            'code': 403,
            'msg': msg
        }

        if data is not None:
            result['data'] = data
        if rows is not None:
            result['rows'] = rows
        if dict_content is not None:
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        result.update({'success': False, 'time': datetime.now()})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )

    @classmethod
    def error(cls, msg: str = '接口异常', data: Optional[Any] = None, rows: Optional[Any] = None,
              dict_content: Optional[Dict] = None, model_content: Optional[BaseModel] = None) -> Response:
        """
        错误响应方法
        :param msg: 可选，自定义错误响应信息
        :param data: 可选，错误响应结果中属性为data的值
        :param rows: 可选，错误响应结果中属性为rows的值
        :param dict_content: 可选，dict类型，错误响应结果中自定义属性的值
        :param model_content: 可选，BaseModel类型，错误响应结果中自定义属性的值
        :return: 错误响应结果
        """
        result = {
            'code': 500,
            'msg': msg
        }

        if data is not None:
            result['data'] = data
        if rows is not None:
            result['rows'] = rows
        if dict_content is not None:
            result.update(dict_content)
        if model_content is not None:
            result.update(model_content.model_dump(by_alias=True))

        result.update({'success': False, 'time': datetime.now()})

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(result)
        )

    @classmethod
    def streaming(cls, *, data: Any = None):
        """
        流式响应方法

        使用 stream 的主要原因是为了处理大文件或长时间运行的请求。
        在这种情况下，将数据以流的形式逐步发送给客户端，而不是一次性加载所有数据，这样可以减少内存消耗和提高响应速度。

        1、节省内存：对于大文件，一次性加载整个文件到内存中会消耗大量内存，可能导致内存不足。使用流可以分块读取和发送数据，减少内存占用。

        2、提高性能：一次性加载大文件可能会导致响应时间过长，使用流可以逐步发送数据，客户端可以更快开始接收和处理数据，提高用户体验。

        3、避免超时：对于需要长时间处理的请求（如生成大文件），一次性处理可能会导致超时错误。使用流可以分段发送数据，减少超时风险。

        :param data: 流式传输的内容
        :return: 流式响应结果
        """
        return StreamingResponse(
            status_code=status.HTTP_200_OK,
            content=data
        )
