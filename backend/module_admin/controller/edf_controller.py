from fastapi import APIRouter
from fastapi import Depends, File
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
                            files: List[UploadFile] = File(...)):
    """
    批量导入Edf文件并添加到数据库
    """
    try:
        upload_results = CommonService.upload_service(request, files)

        # 上传结果汇总
        failed_msgs = []
        success_results = []
        for res in upload_results:
            if res.is_success:
                success_results.append(res)
            else:
                failed_msgs.append(res.message)

        warning_msg = ''
        if failed_msgs:
            warning_msg = ';'.join(failed_msgs)
            logger.warning(warning_msg)
        else:
            logger.info('上传成功')
        if len(failed_msgs) == len(files):
            return ResponseUtil.failure(msg=warning_msg)

        success_edf_list = []
        for res in success_results:
            edf = EdfModel(
                edfName=res.result.original_filename,  # 字典已经转化为了Pydantic模型
                edfPath=res.result.file_path,
                uploadBy=current_user.user.user_name,
                uploadTime=datetime.now()
            )
            success_edf_list.append(edf)

        added_edf = AddEdfModel(edfList=success_edf_list, userId=current_user.user.user_id)
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
