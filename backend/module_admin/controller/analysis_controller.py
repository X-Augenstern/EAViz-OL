from fastapi import APIRouter, Depends, Request
from config.get_db import get_db
from config.env import EAVizConfig
from module_admin.annotation.log_annotation import log_decorator
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_admin.service.edf_service import *
from utils.log_util import *
from utils.response_util import ResponseUtil
from eaviz.ESC_SD.escsd import ESCSD

analysisController = APIRouter(prefix='/eaviz', dependencies=[Depends(LoginService.get_current_user)])


@analysisController.post("/escsd", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:escsd:analyse"))])
@log_decorator(title="EDF分析", business_type=11)
async def anslyse_escsd_by_edf_id(request: Request,
                                  edf_data_analyse: EdfDataAnalyseGenericModel,
                                  query_db: Session = Depends(get_db),
                                  current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    try:
        edf_raw_query = EdfRawQueryModel(edfId=edf_data_analyse.edf_id,
                                         selectedChannels=','.join(EAVizConfig.channels_21))
        edf_raw_query_result = EdfService.get_edf_raw_by_id_services(query_db, edf_raw_query)
        if edf_raw_query_result.is_success:  # 检查是否获取成功
            logger.info(edf_raw_query_result.message)
            raw = edf_raw_query_result.result
            if raw.info['nchan'] == 21:  # 检查通道数量
                if edf_data_analyse.method == "DSMN-ESS":
                    model = request.app.state.models.get('SD')  # todo 与model处协调一下
                    if model:  # 检查模型是否预加载
                        ESCSD.sd(raw, model, edf_data_analyse.start_time)
                        return ResponseUtil.success(msg=f"SD分析完成")
                    else:
                        logger.error(f"对应的预训练模型未加载: {edf_data_analyse.method}")
                        return ResponseUtil.error(msg=f"预训练模型未加载: {edf_data_analyse.method}")
        else:
            return ResponseUtil.error(msg=edf_raw_query_result.message)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))
