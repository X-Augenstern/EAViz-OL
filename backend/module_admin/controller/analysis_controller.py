from asyncio import get_event_loop
from cv2 import VideoCapture, CAP_PROP_FRAME_COUNT, CAP_PROP_FPS
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form
from json import dumps
from os import remove
from tempfile import NamedTemporaryFile

from config.env import EAVizConfig, UploadConfig
from config.get_db import get_db
from module_admin.annotation.log_annotation import log_decorator
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.entity.vo.video_vo import VideoModel, AddVideoModel
from module_admin.service.common_service import CommonService
from module_admin.service.edf_service import *
from module_admin.service.login_service import LoginService
from module_admin.service.video_service import VideoService
from utils.log_util import *
from utils.response_util import ResponseUtil
from eaviz.ESC_SD.escsd import ESCSD
from eaviz.AD.ad import AD
from eaviz.SpiD.spid import SPID
from eaviz.SRD.srd import SRD
from eaviz.VD.vd import VDProcessor

analysisController = APIRouter(prefix='/eaviz', dependencies=[Depends(LoginService.get_current_user)])
download_path = UploadConfig.DOWNLOAD_PATH


@analysisController.post("/escsd", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:escsd:analyse"))])
@log_decorator(title="ESCSD分析", business_type=12)
async def analyse_escsd_by_edf_id(request: Request,
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

        model_name = edf_data_analyse.method
        if model_name not in EAVizConfig.ModelConfig.ESC_SD_MODEL:
            return ResponseUtil.error(msg='模型选择有误')

        model = request.app.state.models.get(model_name)  # todo 与model处协调一下
        if not model:
            logger.error(f"对应的预训练模型未加载: {model_name}")
            return ResponseUtil.error(msg=f"预训练模型未加载: {model_name}")

        fm_abs = None
        stft_abs = None
        res_abs = None
        if model_name == "DSMN-ESS":
            ESCSD.sd(raw, model, edf_data_analyse.start_time)
            fm_abs = EAVizConfig.AddressConfig.get_sd_adr('fm')
            stft_abs = EAVizConfig.AddressConfig.get_sd_adr('stft')
            res_abs = EAVizConfig.AddressConfig.get_sd_adr('res')
        elif model_name == "R3DClassifier":
            ESCSD.esc(raw, model, edf_data_analyse.start_time)
            fm_abs = EAVizConfig.AddressConfig.get_esc_adr('fm')
            stft_abs = EAVizConfig.AddressConfig.get_esc_adr('stft')
            res_abs = EAVizConfig.AddressConfig.get_esc_adr('res')

        # 把目录下的结果图转成 URL（StaticFiles 访问路径）
        # app.mount 只是告诉 FastAPI：URL 前缀 ↔ 硬盘目录 的映射关系。
        # 后端代码里拿到的是 硬盘路径，必须转换成 URL 才能返回给前端。
        image_urls = [
            CommonService.make_static_url(request, fm_abs, download_path),
            CommonService.make_static_url(request, stft_abs, download_path),
            CommonService.make_static_url(request, res_abs, download_path)
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


@analysisController.post("/ad", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:ad:analyse"))])
@log_decorator(title="AD分析", business_type=13)
async def analyse_ad_by_edf_id(request: Request,
                               edf_data_analyse: EdfDataAnalyseADModel,
                               query_db: Session = Depends(get_db),
                               current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    try:
        edf_raw_query = EdfRawQueryModel(edfId=edf_data_analyse.edf_id,
                                         selectedChannels=','.join(EAVizConfig.ChannelEnum.CH19.value))
        edf_raw_query_result = EdfService.get_edf_raw_by_id_services(query_db, edf_raw_query)
        if not edf_raw_query_result.is_success:  # 检查是否获取成功
            return ResponseUtil.error(msg=edf_raw_query_result.message)

        logger.info(edf_raw_query_result.message)
        raw = edf_raw_query_result.result
        if raw.info['nchan'] != 19:  # 检查通道数量
            return ResponseUtil.error(msg='通道数不是 19，无法进行 AD 分析')

        if edf_data_analyse.method not in EAVizConfig.ModelConfig.AD_MODEL:
            return ResponseUtil.error(msg='模型选择有误')

        parse = edf_data_analyse.method.split('_')
        model1, model2 = parse[0], parse[1]
        mod1 = request.app.state.models.get(model1)  # todo 与model处协调一下
        mod2 = request.app.state.models.get(model2)
        if not mod1 or not mod2:
            logger.error(f"对应的预训练模型未加载: {edf_data_analyse.method}")
            return ResponseUtil.error(msg=f"预训练模型未加载: {edf_data_analyse.method}")

        AD.ad(raw, edf_data_analyse.start_time, edf_data_analyse.fb_idx, edf_data_analyse.arti_list, mod1, mod2, model2)

        topo_abs = EAVizConfig.AddressConfig.get_ad_adr('topo')
        res_abs = EAVizConfig.AddressConfig.get_ad_adr('res')

        image_urls = [
            CommonService.make_static_url(request, topo_abs, download_path),
            CommonService.make_static_url(request, res_abs, download_path)
        ]
        image_urls = [u for u in image_urls if u]

        return ResponseUtil.success(data={
            "images": image_urls,
            "message": "分析完成"
        })
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@analysisController.post("/spid", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:spid:analyse"))])
@log_decorator(title="SpiD分析", business_type=14)
async def analyse_spid_by_edf_id(request: Request,
                                 edf_data_analyse: EdfDataAnalyseSpiDModel,
                                 query_db: Session = Depends(get_db),
                                 current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    try:
        edf_raw_query = EdfRawQueryModel(edfId=edf_data_analyse.edf_id,
                                         selectedChannels=','.join(EAVizConfig.ChannelEnum.CH19.value))
        edf_raw_query_result = EdfService.get_edf_raw_by_id_services(query_db, edf_raw_query)
        if not edf_raw_query_result.is_success:  # 检查是否获取成功
            return ResponseUtil.error(msg=edf_raw_query_result.message)

        logger.info(edf_raw_query_result.message)
        raw = edf_raw_query_result.result
        if raw.info['nchan'] != 19:  # 检查通道数量
            return ResponseUtil.error(msg='通道数不是 19，无法进行 SpiD 分析')

        model_name = edf_data_analyse.method
        if model_name not in EAVizConfig.ModelConfig.SpiD_MODEL:
            return ResponseUtil.error(msg='模型选择有误')

        swi = None
        res_abs = None
        if model_name == "Template Matching":
            swi = SPID.tm(raw, edf_data_analyse.start_time, edf_data_analyse.stop_time)
            res_abs = EAVizConfig.AddressConfig.get_spid_adr('res')
        elif model_name == "Unet+ResNet34":
            model = request.app.state.models.get(model_name)  # todo 与model处协调一下
            if not model:
                logger.error(f"对应的预训练模型未加载: {model_name}")
                return ResponseUtil.error(msg=f"预训练模型未加载: {model_name}")

            swi = SPID.ss(raw, model, edf_data_analyse.start_time, edf_data_analyse.stop_time)
            res_abs = EAVizConfig.AddressConfig.get_spid_adr('res')

        image_urls = [
            CommonService.make_static_url(request, res_abs, download_path)
        ]
        image_urls = [u for u in image_urls if u]

        return ResponseUtil.success(data={
            "swi": swi,
            "images": image_urls,
            "message": "分析完成"
        })
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@analysisController.post("/srd", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:srd:analyse"))])
@log_decorator(title="SRD分析", business_type=15)
async def analyse_srd_by_edf_id(request: Request,
                                edf_data_analyse: EdfDataAnalyseSRDModel,
                                query_db: Session = Depends(get_db),
                                current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    流式输出 SRD 分析数据
    """
    try:
        edf_raw_query = EdfRawQueryModel(edfId=edf_data_analyse.edf_id)
        edf_raw_query_result = EdfService.get_edf_raw_by_id_services(query_db, edf_raw_query)
        if not edf_raw_query_result.is_success:  # 检查是否获取成功
            return ResponseUtil.error(msg=edf_raw_query_result.message)

        logger.info(edf_raw_query_result.message)
        raw = edf_raw_query_result.result

        model_name = edf_data_analyse.method
        if model_name not in EAVizConfig.ModelConfig.SRD_MODEL:
            return ResponseUtil.error(msg='模型选择有误')

        model = request.app.state.models.get(model_name)  # todo 与model处协调一下
        if not model:
            logger.error(f"对应的预训练模型未加载: {model_name}")
            return ResponseUtil.error(msg=f"预训练模型未加载: {model_name}")

        # 生成流式数据
        stream_generator = SRD.stream_srd_data(
            raw, model,
            edf_data_analyse.start_time,
            edf_data_analyse.stop_time,
            edf_data_analyse.ch_idx,
            UploadConfig.STREAM_WINDOW_SIZE_SECOND
        )
        return ResponseUtil.streaming(data=stream_generator)
    except Exception as e:
        logger.exception(e)
        return ResponseUtil.error(msg=str(e))


@analysisController.post("/vd", dependencies=[Depends(CheckUserInterfaceAuth("eaviz:vd:analyse"))])
@log_decorator(title="VD分析", business_type=16)
async def analyse_vd_by_video_path(
        request: Request,
        video_files: List[UploadFile] = File(..., description="一个或多个MP4视频文件"),
        conf_thres: float = Form(EAVizConfig.VDConfig.CONF_THRES),
        iou_thres: float = Form(EAVizConfig.VDConfig.IOU_THRES),
        query_db: Session = Depends(get_db),
        current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    """
    VD视频分析接口
    每个上传的视频都会被保存为临时文件，分析完成后自动删除。
    使用FastAPI的线程池执行器处理CPU/GPU密集型任务，支持多个用户并发请求。
    """
    if not video_files:
        return ResponseUtil.error(msg="请至少上传一个视频文件")

    tmp_files: List[tuple[str, str]] = []  # [(tmp_path, original_name)]
    try:
        # 验证视频文件格式（只支持MP4），并保存到临时文件
        for video_file in video_files:
            if not video_file.filename or not video_file.filename.lower().endswith('.mp4'):
                return ResponseUtil.error(msg=f"文件 {video_file.filename} 不是MP4格式")

            with NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_path = tmp_file.name
                while chunk := await video_file.read(1024 * 1024 * 10):  # 每次读取10MB
                    tmp_file.write(chunk)
            tmp_files.append((tmp_path, video_file.filename))
            logger.info(
                f"analysis_controller:analyse_vd_by_video_path 视频文件已保存到临时文件: {tmp_path}, 原始文件名: {video_file.filename}, "
                f"文件大小: {path.getsize(tmp_path)} bytes")

        # 解析并校验检测阈值（限制在0~1范围内）
        def _clamp_01(value: float, default: float) -> float:
            try:
                v = float(value)
            except (TypeError, ValueError):
                return default
            if v < 0.0:
                return 0.0
            if v > 1.0:
                return 1.0
            return v

        conf_thres = _clamp_01(conf_thres, EAVizConfig.VDConfig.CONF_THRES)
        iou_thres = _clamp_01(iou_thres, EAVizConfig.VDConfig.IOU_THRES)
        logger.info(
            f"analysis_controller:analyse_vd_by_video_path VD检测阈值: conf_thres={conf_thres}, iou_thres={iou_thres}")

        # 统一保存处理后视频到 VD/res 目录
        output_adr = EAVizConfig.AddressConfig.get_vd_adr("res")
        logger.info(
            f"analysis_controller:analyse_vd_by_video_path VD处理结果将保存到目录: {output_adr}, 目录是否存在: {path.exists(output_adr)}")
        video_paths = [t[0] for t in tmp_files]
        logger.info(
            f"analysis_controller:analyse_vd_by_video_path 开始处理VD视频分析, 共 {len(video_paths)} 个视频, output_adr={output_adr}")

        # 获取模型
        method = EAVizConfig.ModelConfig.VD_MODEL[0]
        parse = method.split('_')
        detect_model, action_model = parse[0], parse[1]
        detect_model = request.app.state.models.get(detect_model)
        action_model = request.app.state.models.get(action_model)
        if not detect_model or not action_model:
            logger.error(f"analysis_controller:analyse_vd_by_video_path 对应的预训练模型未加载: {method}")
            return ResponseUtil.error(msg=f"预训练模型未加载: {method}")

        # 创建VD处理器（使用本次请求指定的阈值）
        processor = VDProcessor(
            detect_model=detect_model,
            action_model=action_model,
            conf_thres=conf_thres,
            iou_thres=iou_thres
        )
        loop = get_event_loop()
        executor = request.app.state.vd_executor
        # 在线程池中执行批量视频处理任务（VDProcessor内部再做并发）
        results = await loop.run_in_executor(
            executor,
            processor.process_videos,
            video_paths,
            output_adr,
            EAVizConfig.VDConfig.VD_EXECUTOR_MAX_WORKERS
        )
        logger.info(f"analysis_controller:analyse_vd_by_video_path VD视频批量处理完成，共 {len(results)} 个结果")

        # 处理VD分析结果
        videos_data = []
        all_success = True
        for (tmp_path, original_name), result in zip(tmp_files, results):
            success = result.get('success', False)
            if not success:
                all_success = False
                logger.error(
                    f"analysis_controller:analyse_vd_by_video_path 视频处理失败: {original_name}, message={result.get('message')}")

            output_url = None
            output_path = result.get('output_path')
            if output_path and success:
                # 保存处理后的视频文件（重命名并保存到VD/res目录）
                save_res = VideoService.save_processed_video_services(output_path, original_name, output_adr)
                if not save_res.is_success:
                    logger.error(
                        f"analysis_controller:analyse_vd_by_video_path 保存处理后的视频文件失败: {save_res.message}")
                else:
                    # 更新output_path为新的保存路径
                    output_path = save_res.result.file_path
                    # 生成URL
                    output_url = CommonService.make_static_url(request, output_path, download_path)
                    logger.info(
                        f"analysis_controller:analyse_vd_by_video_path 处理后的视频已保存: {output_path}，生成的视频URL: {output_url}")
                    if not output_url:
                        logger.warning(
                            f"analysis_controller:analyse_vd_by_video_path 无法生成视频URL，路径: {output_path}")

                    await VideoService.cache_processed_video_services(request, output_path, output_url, original_name)

                    # 保存视频信息到数据库（与EDF的处理方式一致）
                    try:
                        # 获取视频文件信息
                        video_name = save_res.result.original_filename
                        video_size = path.getsize(output_path) if path.exists(output_path) else 0
                        video_time = 0.0

                        # 获取视频时长
                        cap = VideoCapture(output_path)
                        if cap.isOpened():
                            frame_count = cap.get(CAP_PROP_FRAME_COUNT)
                            fps = cap.get(CAP_PROP_FPS)
                            if fps > 0:
                                video_time = frame_count / fps
                            cap.release()

                        # 序列化分析结果
                        analysis_results = result.get('results', [])
                        video_res = dumps(analysis_results, ensure_ascii=False) if analysis_results else ''

                        # 创建视频模型（与EDF的处理方式一致）
                        video_model = VideoModel(
                            videoName=video_name,
                            videoSize=video_size,
                            videoTime=video_time,
                            videoPath=output_path,
                            videoRes=video_res,
                            uploadBy=current_user.user.user_name,
                            uploadTime=datetime.now()
                        )

                        # 保存到数据库（与EDF的处理方式一致）
                        add_video_model = AddVideoModel(videoList=[video_model], userId=current_user.user.user_id)
                        add_result = VideoService.add_video_services(query_db, add_video_model)
                        if add_result.is_success:
                            logger.info(
                                f"analysis_controller:analyse_vd_by_video_path 视频信息已保存到数据库: {video_name}")
                        else:
                            logger.warning(
                                f"analysis_controller:analyse_vd_by_video_path 保存视频信息到数据库失败: {add_result.message}")
                    except Exception as e:
                        logger.error(
                            f"analysis_controller:analyse_vd_by_video_path 保存视频信息到数据库时出错: {str(e)}")
                        logger.exception(f"analysis_controller:analyse_vd_by_video_path {e}")

            videos_data.append({
                "video_name": original_name,
                "tmp_path": tmp_path,
                "output_url": output_url,
                "results": result.get('results', []),
                "success": success,
                "message": result.get('message', '处理完成' if success else '处理失败')
            })

        return ResponseUtil.success(data={
            "videos": videos_data,
            "message": "全部视频处理完成" if all_success else "部分视频处理失败，请检查结果"
        })

    except Exception as e:
        logger.exception(f"analysis_controller:analyse_vd_by_video_path {e}")
        return ResponseUtil.error(msg=str(e))
    finally:
        # 删除所有临时文件
        for tmp_path, original_name in tmp_files:
            if tmp_path and path.exists(tmp_path):
                try:
                    remove(tmp_path)
                    logger.info(
                        f"analysis_controller:analyse_vd_by_video_path 临时文件已删除: {tmp_path}, 原始文件名: {original_name}")
                except Exception as e:
                    logger.warning(
                        f"analysis_controller:analyse_vd_by_video_path 删除临时文件失败: {tmp_path}, 错误: {str(e)}")
