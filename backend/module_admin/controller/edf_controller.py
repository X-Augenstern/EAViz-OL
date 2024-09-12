from fastapi import APIRouter, Depends, File, Body
from config.get_db import get_db
from module_admin.service.login_service import LoginService, CurrentUserModel
from module_admin.service.common_service import *
from module_admin.service.edf_service import *
from utils.response_util import *
from utils.log_util import *
from utils.page_util import PageResponseModel
from module_admin.annotation.log_annotation import log_decorator
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from os import path, remove
from utils.common_util import data2bytes_response

edfController = APIRouter(prefix='/system/edf', dependencies=[Depends(LoginService.get_current_user)])


@edfController.get("/list", response_model=PageResponseModel,
                   dependencies=[Depends(CheckUserInterfaceAuth('system:edf:list'))])
async def get_system_edf_list(request: Request, edf_page_query: EdfPageQueryModel = Depends(EdfPageQueryModel.as_query),
                              query_db: Session = Depends(get_db),
                              current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取Edf列表分页数据
    """
    try:
        edf_page_query_result = EdfService.get_edf_list_services(query_db, current_user.user.user_id, edf_page_query,
                                                                 is_page=True)
        logger.info('获取成功')
        return ResponseUtil.success(model_content=edf_page_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@edfController.get("/{edf_id}", response_model=EdfModel,
                   dependencies=[Depends(CheckUserInterfaceAuth('system:edf:query'))])
async def query_detail_system_edf(request: Request, edf_id: int, query_db: Session = Depends(get_db)):
    """
    根据Edf的id获取Edf详细信息
    """
    try:
        edf_detail_result = EdfService.get_edf_by_id_services(query_db, edf_id)
        logger.info(f'获取edf_id 为{edf_id}的信息成功')
        return ResponseUtil.success(data=edf_detail_result.model_dump(by_alias=True))
    except Exception as e:
        return ResponseUtil.error(msg=str(e))


@edfController.get("/{user_id}", response_model=PageResponseModel,
                   dependencies=[Depends(CheckUserInterfaceAuth('system:edf:query'))])
async def query_detail_system_edf(request: Request,
                                  edf_user_page_query: EdfUserPageQueryModel = Depends(EdfUserPageQueryModel.as_query),
                                  query_db: Session = Depends(get_db)):
    """
    根据用户的id获取Edf详细信息
    """
    try:
        edf_user_page_query_result = EdfService.get_edf_list_by_user_id_services(query_db, edf_user_page_query,
                                                                                 is_page=True)
        logger.info('获取成功')
        return ResponseUtil.success(model_content=edf_user_page_query_result)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@edfController.post("/importData", dependencies=[Depends(CheckUserInterfaceAuth("system:edf:import"))])
@log_decorator(title='EDF管理', business_type=6)
async def import_system_edf(request: Request, query_db: Session = Depends(get_db),
                            current_user: CurrentUserModel = Depends(LoginService.get_current_user),
                            file: UploadFile = File(...)):
    """
    导入Edf文件并添加到数据库
    """
    try:
        upload_res = CommonService.upload_service(request, file)

        # 检查上传结果
        if not upload_res.is_success:
            logger.warning(upload_res.message)
            return ResponseUtil.failure(msg=upload_res.message)
        logger.info(upload_res.message)

        edf = EdfModel(
            edfName=upload_res.result.original_filename,  # 字典已经转化为了Pydantic模型
            edfSfreq=upload_res.result.extra_info['sfreq'],
            edfTime=upload_res.result.extra_info['time'],
            edfPath=upload_res.result.file_path,
            validChannels=upload_res.result.extra_info['valid_channels'],
            uploadBy=current_user.user.user_name,
            uploadTime=datetime.now()
        )

        added_edf = AddEdfModel(edfList=[edf], userId=current_user.user.user_id)
        added_edf_result = EdfService.add_edf_services(query_db, added_edf)
        if added_edf_result.is_success:
            logger.info(added_edf_result.message)
            return ResponseUtil.success(msg=added_edf_result.message)
        else:
            logger.warning(added_edf_result.message)
            return ResponseUtil.failure(msg=added_edf_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@edfController.delete("/{edf_ids}", dependencies=[Depends(CheckUserInterfaceAuth("system:edf:remove"))])
@log_decorator(title='EDF管理', business_type=3)
async def delete_system_edf(request: Request, edf_ids: str, query_db: Session = Depends(get_db),
                            current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    删除Edf文件并从数据库中删除记录
    """
    if edf_ids:
        edf_id_list = edf_ids.split(',')
        try:
            for edf_id in edf_id_list:
                edf_detail_result = EdfService.get_edf_by_id_services(query_db, int(edf_id))
                if edf_detail_result:
                    file_path = edf_detail_result.edf_path
                    if path.exists(file_path):
                        remove(file_path)
                        logger.info(f'文件 {file_path} 删除成功')
                    else:
                        logger.warning(f'文件 {file_path} 不存在或已被删除')
                else:
                    logger.warning(f'EDF ID {edf_id} 未找到')

            delete_edf = DeleteEdfModel(edfIds=edf_ids)
            delete_edf_result = EdfService.delete_edf_services(query_db, delete_edf)
            if delete_edf_result.is_success:
                logger.info(delete_edf_result.message)
                return ResponseUtil.success(msg=delete_edf_result.message)
            else:
                logger.warning(delete_edf_result.message)
                return ResponseUtil.failure(msg=delete_edf_result.message)
        except Exception as e:
            logger.exception(e)
            return ResponseUtil.error(msg=str(e))
    else:
        return ResponseUtil.error(msg='传入EDF ID为空')


@edfController.post("/getData", dependencies=[Depends(CheckUserInterfaceAuth("system:edf:getData"))])
@log_decorator(title='EDF管理', business_type=10)
async def get_system_edf_data_by_id(request: Request,
                                    edf_data_query: EdfDataQueryModel = Body(...),
                                    query_db: Session = Depends(get_db),
                                    current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    获取Edf数据

    1、路径参数："/{edf_ids}"
    直接在路由路径中定义，属于URL的一部分。由FastAPI自动解析并传递给对应的函数参数。
        路径：/{edf_ids}，在路径中定义了参数edf_ids。
        路径参数：通过URL路径传递，如：/123,456。
        路径参数解析：edf_ids参数由FastAPI自动解析并传递给函数。
    路径参数通常用于标识资源或指定资源的层次结构。路径参数是URL的一部分，通常用于需要唯一标识某个特定资源的场合。
        获取、更新或删除特定资源。
        资源层次结构（如目录和子目录）。
        e.g.:
            获取用户详情：/users/{user_id}
            删除特定的EDF数据：/system/edf/{edf_ids}

    2、查询参数："/getData" edf_data_query: EdfDataQueryModel = Depends(EdfDataQueryModel.as_query)
    不在路径中定义，而是通过URL中的查询字符串传递。
    通过FastAPI的Query注解解析，或者通过依赖项注入传递给函数参数。
        路径：/getData，没有在路径中定义参数。
        查询参数：通过URL查询字符串传递，如：/getData?edf_id=123&selected_channels=channel1,channel2。
        依赖项注入：edf_data_query参数通过Depends(EdfDataQueryModel.as_query)注入，该方法解析查询字符串中的参数并创建EdfDataQueryModel实例。
    查询参数通常用于过滤、排序或分页等目的，它们是附加在URL之后的键值对。查询参数适用于传递可选参数或多个参数的情况。
        过滤、排序或分页。
        可选参数（如搜索条件）。
        一次性查询多个属性。
        e.g.:
            获取过滤后的EDF数据：/system/edf/getData?edf_id=123&selected_channels=channel1,channel2
            搜索用户：/users?name=john&age=30

    3、请求体参数："/getData" edf_data_query: EdfDataQueryModel = Body(...)
    请求体参数通过POST请求的请求体传递，不在路径或查询字符串中定义。
    Body(...) 告诉 FastAPI 从请求体中读取 edf_data_query 参数。... 是一个特殊的值，表示这个参数是必需的。
    通过Pydantic模型解析请求体数据并传递给函数参数。
        路径：/getData，没有在路径中定义参数，路径是固定的。
        请求体参数：通过POST请求的请求体传递，如：
        {
            "edfId": 123,
            "selectedChannels": "channel1, channel2"
        }
    请求体参数通常用于：
        传递需要创建、更新或复杂查询的完整数据。
        包含大量或敏感信息。
        结构化的数据传递。

    路径参数：用于标识资源或资源层次结构。
    查询参数：用于过滤、排序、分页或传递可选参数。
    请求体参数：用于传递复杂数据结构或表单数据。
    标头参数：用于传递认证信息或自定义HTTP标头。
    Cookie参数：用于维护用户会话状态或存储用户偏好设置。
    表单参数：用于处理HTML表单提交的数据或文件上传。

    在GET请求中，使用请求体参数（Body Parameters）是不符合HTTP规范的。
    在RESTful设计中，GET请求是设计用来从服务器获取资源的，它应该是无副作用的请求，并且不允许请求体。应当仅使用路径参数和查询参数。
    使用请求体参数通常适用于POST、PUT和PATCH请求，用于传递大量数据或复杂的结构化数据。
    而POST请求通常用于可能引起副作用的写入操作。
    尽管GET请求是最常见的读取数据的方法，使用POST请求读取数据在某些情况下也是可以接受的，特别是在以下情况：
        请求参数复杂且数量较多：如果请求参数复杂且数量较多，GET请求的URL长度可能会受到限制。
        敏感数据：如果请求参数中包含敏感数据，不希望在URL中暴露这些信息，可以使用POST请求将参数放在请求体中。
        即使GET请求是读取操作的标准选择，在实际应用中使用POST请求来读取数据也并非不可能。许多API在处理复杂查询时都使用POST请求。
    GET请求是无副作用的读取操作的标准选择，但受到URL长度限制和数据保密问题的影响。
    POST请求可以在需要传递复杂和大量参数或需要保密数据时使用，即使是无副作用的读取操作。

    使用 Depends 是为了依赖注入的便利，它可以自动处理请求参数的解析。但是，Depends 默认从查询参数、路径参数等来源解析参数，而不是从请求体中解析参数。
    若参数是通过请求体发送的，需要明确告诉 FastAPI 从请求体中解析参数。这就需要使用 Body。
    """
    try:
        edf_data_query_result = EdfService.get_edf_data_by_id_services(query_db, edf_data_query)
        if edf_data_query_result.is_success:
            logger.info(edf_data_query_result.message)
            return ResponseUtil.streaming(data=data2bytes_response(edf_data_query_result.result))
        else:
            return ResponseUtil.error(msg=edf_data_query_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
