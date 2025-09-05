from pathlib import Path
from fastapi import APIRouter, Depends, Request
from config.get_db import get_db
from config.env import EAVizConfig, UploadConfig
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
                                         selectedChannels=','.join(EAVizConfig.ChannelEnum.CH21.value))
        edf_raw_query_result = EdfService.get_edf_raw_by_id_services(query_db, edf_raw_query)
        if not edf_raw_query_result.is_success:  # 检查是否获取成功
            return ResponseUtil.error(msg=edf_raw_query_result.message)

        logger.info(edf_raw_query_result.message)
        raw = edf_raw_query_result.result
        if raw.info['nchan'] != 21:  # 检查通道数量
            return ResponseUtil.error(msg='通道数不是 21，无法进行 ESC/SD 分析')

        if edf_data_analyse.method == "DSMN-ESS":
            model = request.app.state.models.get('SD')  # todo 与model处协调一下
            if not model:
                logger.error(f"对应的预训练模型未加载: {edf_data_analyse.method}")
                return ResponseUtil.error(msg=f"预训练模型未加载: {edf_data_analyse.method}")

            ESCSD.sd(raw, model, edf_data_analyse.start_time)

            fm_abs = EAVizConfig.AddressConfig.get_sd_adr('fm')
            stft_abs = EAVizConfig.AddressConfig.get_sd_adr('stft')
            res_abs = EAVizConfig.AddressConfig.get_sd_adr('res')
        else:
            model = request.app.state.models.get('ESC')
            if not model:
                logger.error(f"对应的预训练模型未加载: {edf_data_analyse.method}")
                return ResponseUtil.error(msg=f"预训练模型未加载: {edf_data_analyse.method}")

            ESCSD.esc(raw, model, edf_data_analyse.start_time)

            fm_abs = EAVizConfig.AddressConfig.get_esc_adr('fm')
            stft_abs = EAVizConfig.AddressConfig.get_esc_adr('stft')
            res_abs = EAVizConfig.AddressConfig.get_esc_adr('res')

        # 把目录下的结果图转成 URL（StaticFiles 访问路径）
        # app.mount 只是告诉 FastAPI：URL 前缀 ↔ 硬盘目录 的映射关系。
        # 后端代码里拿到的是 硬盘路径，必须转换成 URL 才能返回给前端。
        image_urls = [
            make_static_url(request, fm_abs),
            make_static_url(request, stft_abs),
            make_static_url(request, res_abs)
        ]
        # 过滤掉没转换成功的
        image_urls = [u for u in image_urls if u]

        return ResponseUtil.success(data={
            "images": image_urls,
            "message": "分析完成"
        })
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


def make_static_url(request: Request, abs_path: str) -> str:
    try:
        p = Path(abs_path).resolve()
        base = Path(UploadConfig.DOWNLOAD_PATH).resolve()
        rel = p.relative_to(base).as_posix()

        root_path = request.scope.get("root_path", "")  # "/dev-api" 或 ""
        prefix = UploadConfig.DOWNLOAD_PREFIX.rstrip("/")  # "/download"

        return f"{root_path}{prefix}/{rel}"
    except Exception as e:
        logger.error(f"无法转换路径为URL: {abs_path}, 错误: {e}")
        return ""

