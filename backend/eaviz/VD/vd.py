from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil
from os import path, makedirs
from typing import List, Callable, Optional, Dict, Any
from threading import Lock
from cv2 import CAP_PROP_FRAME_COUNT, CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT, resize, VideoWriter, VideoCapture
from torch import device
from eaviz.VD.Pre_videodata import LoadVideos
from eaviz.VD.api import Colors, annotating_box, actionRecognition, non_max_suppression, scale_coords
from eaviz.VD.config import Config
from utils.log_util import logger


class VDProcessor:
    """
    VD视频分析处理器（在线版本）
    支持并发处理多个视频，使用回调函数替代信号机制
    Be careful that input_list can not be None。
    """

    def __init__(self,
                 detect_model=None,
                 action_model=None,
                 progress_callback: Optional[Callable] = None):
        """
        初始化VD处理器
        
        Args:
            detect_model: 检测模型
            action_model: 动作识别模型
            progress_callback: 进度回调函数，接收(percent, video_path)参数
        """
        self.detectModel = detect_model
        self.actionModel = action_model
        self.progress_callback = progress_callback

        self.cfg = Config()
        self.conf_thres = 0.25  # 置信度
        self.iou_thres = 0.45  # iou
        self.device = device(self.cfg.device)
        self.color = Colors()

        # 每个视频处理任务的独立状态
        self._task_states: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()  # 用于保护共享状态

    def _get_task_state(self, video_path: str) -> Dict[str, Any]:
        """获取或创建任务状态"""
        with self._lock:
            if video_path not in self._task_states:
                self._task_states[video_path] = {
                    'last_box': None,
                    'features': [],
                    'output_frames': [],
                    'cnt': 0,
                    'vid_cap': None,
                    'video_size': None  # 保存视频尺寸，避免vid_cap释放后无法获取
                }
            return self._task_states[video_path]

    def _update_progress(self, video_path: str, cnt: int, total_frames: int):
        """更新进度"""
        if total_frames > 0:
            percent = int(cnt / total_frames * 100)
            if self.progress_callback:
                self.progress_callback(percent, video_path)

    def _process_image(self, img, img0, state: Dict[str, Any]):
        """处理单帧图像"""
        state['last_box'], xyxy = self._detect(img, img0, state['last_box'])
        im = img0.copy()
        if state['last_box'] is None:  # 未检测到患者
            state['output_frames'].append(im)
        else:
            out = annotating_box(img0, xyxy, color=self.color(1, True), line_width=self.cfg.line_thickness)
            state['output_frames'].append(out)
            # 将处理后的图像中特定区域的特征保存起来
            state['features'].append(resize(im[int(xyxy[1]):int(xyxy[3]), int(xyxy[0]):int(xyxy[2])], (112, 112)))

    def _detect(self, img, img0, last_box):
        """执行目标检测"""
        pred, featuremap = self.detectModel(img, augment=False, visualize=False)
        pred = non_max_suppression([pred[0], pred[2]], self.conf_thres, self.iou_thres, None, False, max_det=5)

        if pred is not None and len(pred) > 0:
            pred = sorted(pred, key=lambda x: x[0][4], reverse=True)[0]
            last_box = pred.clone()
        elif last_box is not None:
            pred = last_box.clone()
        else:
            return None, None

        pred[:, :4] = scale_coords(img.shape[2:], pred[:, :4], img0.shape).round()
        *xyxy, conf, cls = pred[0]  # 星号表达式 将 pred[0] 中的前几个元素赋值给一个名为 xyxy 的列表
        return last_box, xyxy

    def _video_changed(self, video_path: str, video_size, state: Dict[str, Any], output_adr: Optional[str] = None,
                       thread_pool: Optional[ThreadPoolExecutor] = None):
        """
        视频切换回调函数（用于处理多个视频的场景）
        注意：对于单个视频，此回调在视频读取完毕时会被调用，但此时不应该清空output_frames
        因为单个视频的保存逻辑在process_video的最后统一处理
        """
        # 重置状态（但不清空output_frames，因为单个视频还需要在最后保存）
        state['last_box'] = None
        state['features'] = []
        state['cnt'] = 0

        # 注意：对于单个视频，LoadVideos在视频读取完毕时会调用此回调
        # 但此时不应该保存或清空output_frames，因为process_video会在最后统一处理
        # 只有在处理多个视频时，才需要在这里保存上一个视频
        # 由于当前实现只处理单个视频，这里不做任何保存操作
        logger.debug(
            f"_video_changed被调用: video_path={video_path}, output_frames数量={len(state.get('output_frames', []))}")

    @staticmethod
    def _save_video(output_path: str, output_frames: List, output_size: tuple):
        """保存视频到文件（参考原先的VDWriteThread实现）"""
        logger.info(f"_save_video被调用: output_path={output_path}, 帧数={len(output_frames)}, 尺寸={output_size}")

        if not output_frames or len(output_frames) == 0:
            logger.error(f"output_frames为空，无法保存视频: {output_path}")
            raise ValueError(f"output_frames为空，无法保存视频")

        # 使用avc1编码
        fourcc = VideoWriter.fourcc(*"avc1")
        output_video = VideoWriter(output_path, fourcc, 20, output_size)
        if not output_video.isOpened():
            logger.error(f"无法创建视频写入器: {output_path}, fourcc={fourcc}, fps=20, size={output_size}")
            raise RuntimeError(f"无法创建视频写入器: {output_path}")
        try:
            logger.info(f"开始写入视频帧，共 {len(output_frames)} 帧")
            for i, frame in enumerate(output_frames):
                if frame is None:
                    logger.warning(f"第 {i} 帧为 None，跳过")
                    continue
                output_video.write(frame)
            logger.info(f"视频写入完成: {output_path}, 已写入 {len(output_frames)} 帧")
        except Exception as e:
            logger.error(f"写入视频帧时出错: {output_path}, 错误: {str(e)}")
            raise
        finally:
            output_video.release()
            # 验证文件是否成功创建
            if path.exists(output_path):
                file_size = path.getsize(output_path)
                logger.info(f"视频文件已创建: {output_path}, 文件大小: {file_size} bytes")
                if file_size == 0:
                    logger.error(f"警告：视频文件大小为0，可能保存失败: {output_path}")
            else:
                logger.error(f"错误：视频文件未创建: {output_path}")

    def process_video(self, video_path: str, output_adr: Optional[str] = None) -> Dict[str, Any]:
        """
        处理单个视频
        
        Args:
            video_path: 视频文件路径
            output_adr: 输出目录（可选）
            
        Returns:
            处理结果字典，包含：
            - success: 是否成功
            - video_path: 视频路径
            - output_path: 输出视频路径（如果保存）
            - results: 动作识别结果列表
            - message: 消息
        """
        # 验证视频文件是否存在
        if not path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return {
                'success': False,
                'video_path': video_path,
                'message': f'视频文件不存在: {video_path}'
            }

        # 验证视频文件是否可以打开
        test_cap = VideoCapture(video_path)
        if not test_cap.isOpened():
            test_cap.release()
            logger.error(f"无法打开视频文件: {video_path}")
            return {
                'success': False,
                'video_path': video_path,
                'message': f'无法打开视频文件: {video_path}'
            }
        test_cap.release()

        state = self._get_task_state(video_path)
        results = []
        try:
            stride = self.detectModel.stride
            dataset = LoadVideos(
                Config(),
                [video_path],
                stride=stride,
                next_video_callback=lambda path, size: self._video_changed(path, size, state, output_adr)
            )
            dataset = iter(dataset)

            frame_count = 0
            while True:
                try:
                    p, img, img0, vid_cap = next(dataset)
                    state['vid_cap'] = vid_cap
                    state['cnt'] += 1
                    frame_count += 1

                    # 更新进度并保存视频尺寸（只在第一次获取）
                    if vid_cap and state.get('video_size') is None:
                        total_frames = vid_cap.get(CAP_PROP_FRAME_COUNT)
                        video_width = int(vid_cap.get(CAP_PROP_FRAME_WIDTH))
                        video_height = int(vid_cap.get(CAP_PROP_FRAME_HEIGHT))
                        state['video_size'] = (video_width, video_height)
                        logger.info(f"获取视频尺寸: {state['video_size']}, 总帧数: {total_frames}")
                        self._update_progress(video_path, state['cnt'], total_frames)
                    elif vid_cap:
                        total_frames = vid_cap.get(CAP_PROP_FRAME_COUNT)
                        self._update_progress(video_path, state['cnt'], total_frames)

                    # 处理图像
                    self._process_image(img, img0, state)

                    # 收集结果
                    if state['cnt'] % 60 == 0 and state['cnt'] > 0 and state['features']:
                        if self.actionModel:
                            res = actionRecognition(self.actionModel, state['features'], self.device)
                            cur_second = state['cnt'] / 20
                            results.append({
                                'time_range': f'{cur_second - 3:.1f}-{cur_second:.1f}s',
                                'action': res
                            })
                            state['features'] = []
                except StopIteration:
                    break

            # 检查是否处理了任何帧
            if frame_count == 0:
                logger.error(f"视频文件无法读取任何帧: {video_path}")
                return {
                    'success': False,
                    'video_path': video_path,
                    'message': f'视频文件无法读取任何帧，请检查视频文件是否损坏'
                }

            logger.info(
                f"视频处理完成: {video_path}, 处理了 {frame_count} 帧, output_frames数量: {len(state.get('output_frames', []))}")

            # 如果未生成任何结果，添加默认分析文本
            if not results:
                total_duration = frame_count / 20 if frame_count > 0 else 0
                placeholder = {
                    'time_range': f'0-{total_duration:.1f}s',
                    'action': '未检测到明显发作特征'
                }
                results.append(placeholder)
                logger.info(f"未检测到有效动作特征，返回默认分析文本: {placeholder}")

            # 处理最后一个视频的保存
            if output_adr:
                logger.info(f"输出目录已指定: {output_adr}")
                if state.get('output_frames') and len(state['output_frames']) > 0:
                    # 优先使用保存的视频尺寸，如果不存在则从vid_cap获取，最后从第一帧获取
                    if state.get('video_size') and state['video_size'][0] > 0 and state['video_size'][1] > 0:
                        video_size = state['video_size']
                        logger.info(f"使用保存的视频尺寸: {video_size}")
                    elif state.get('vid_cap'):
                        try:
                            video_width = int(state['vid_cap'].get(CAP_PROP_FRAME_WIDTH))
                            video_height = int(state['vid_cap'].get(CAP_PROP_FRAME_HEIGHT))
                            if video_width > 0 and video_height > 0:
                                video_size = (video_width, video_height)
                                logger.info(f"从vid_cap获取视频尺寸: {video_size}")
                            else:
                                raise ValueError("vid_cap返回的尺寸无效")
                        except Exception as e:
                            logger.warning(f"从vid_cap获取尺寸失败: {str(e)}，尝试从第一帧获取")
                            video_size = (state['output_frames'][0].shape[1], state['output_frames'][0].shape[0])
                            logger.info(f"从第一帧获取视频尺寸: {video_size}")
                    else:
                        # 从第一帧获取尺寸
                        video_size = (state['output_frames'][0].shape[1], state['output_frames'][0].shape[0])
                        logger.info(f"从第一帧获取视频尺寸: {video_size}")

                    # 验证视频尺寸
                    if video_size[0] <= 0 or video_size[1] <= 0:
                        logger.error(f"视频尺寸无效: {video_size}，无法保存视频")
                        output_path = None
                    else:
                        output_name = path.splitext(path.basename(video_path))[0]
                        output_path = path.abspath(path.join(output_adr, output_name + '_VD_processed.mp4'))
                        logger.info(
                            f"开始保存处理后的视频: {output_path}, 帧数: {len(state['output_frames'])}, 尺寸: {video_size}")
                        try:
                            self._save_video(output_path, state['output_frames'], video_size)
                            logger.info(f"视频保存成功: {output_path}")
                        except Exception as e:
                            logger.error(f"保存视频失败: {output_path}, 错误: {str(e)}")
                            output_path = None
                else:
                    logger.warning(
                        f"output_frames为空或长度为0，无法保存视频: {video_path}, output_frames: {state.get('output_frames')}")
                    output_path = None
            else:
                logger.info(f"未指定输出目录，不保存视频: {video_path}")
                output_path = None

            # 清理状态
            if state['vid_cap']:
                state['vid_cap'].release()

            return {
                'success': True,
                'video_path': video_path,
                'output_path': output_path,
                'results': results,
                'message': '处理完成'
            }
        except Exception as e:
            return {
                'success': False,
                'video_path': video_path,
                'message': f'处理失败: {str(e)}'
            }
        finally:
            # 清理任务状态
            with self._lock:
                if video_path in self._task_states:
                    del self._task_states[video_path]

    def process_videos(self, video_paths: List[str], output_adr: Optional[str] = None, max_workers: int = 5) -> List[
        Dict[str, Any]]:
        """
        并发处理多个视频
        
        Args:
            video_paths: 视频文件路径列表
            output_adr: 输出目录（可选）
            max_workers: 最大并发数，默认5
            
        Returns:
            处理结果列表
        """
        if not video_paths:
            return []

        # 限制并发数
        workers = min(max_workers, len(video_paths))
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # 提交所有任务
            future_to_video = {
                executor.submit(self.process_video, video_path, output_adr): video_path
                for video_path in video_paths
            }

            # 收集结果
            for future in as_completed(future_to_video):
                video_path = future_to_video[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'video_path': video_path,
                        'message': f'处理异常: {str(e)}'
                    })

        return results
