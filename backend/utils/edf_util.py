from typing import List
from config.env import EAVizConfig
from numpy import array
from mne import channels, io
from utils.log_util import logger
from os import remove


class EdfUtil:
    """
    Edf工具类
    """

    @classmethod
    def map_channels(cls, selected_channels: List, raw_channels: List):
        """
        将raw中的通道映射为统一的通道名
        """
        # 获得selected_channels在raw_edf上的映射：mapping_list（目标：数量相等，名字对应）
        tmp_channels = selected_channels.copy()
        mapping_list = []
        for key in tmp_channels:
            tmp = []
            for ch_name in raw_channels:
                if key in ch_name:
                    tmp.append(ch_name)
            if len(tmp) == 0:  # 选择 > 存在
                selected_channels.remove(key)
            elif len(tmp) == 1:  # 选择 = 存在
                mapping_list.extend(tmp)
            else:  # 选择 < 存在：存在相近的通道名，则只保留最短的
                tmp = [ch_name for ch_name in tmp if len(ch_name) == min(len(ch) for ch in tmp)]
                if len(tmp) == 1:
                    mapping_list.extend(tmp)
                else:  # 存在两条名字相同的通道：直接报异常
                    mapping_list = []
                    break
        return selected_channels, mapping_list

    @classmethod
    def normalize_edf(cls, edf_path: str, selected_channels: str = None):
        """
        按规定的21通道名及通道顺序调整edf格式。若规范失败，直接删除上传文件。
        """
        try:
            if not selected_channels:
                # 列表是通过引用传递的，当后面修改 selected_channels 的内容时，实际上修改的是 EAVizConfig.channels_21
                selected_channels = EAVizConfig.channels_21.copy()
            else:
                selected_channels = selected_channels.split(',')

            raw = io.read_raw_edf(edf_path, preload=True)
            raw_channels = raw.info['ch_names']

            selected_channels, mapping_list = EdfUtil.map_channels(selected_channels, raw_channels)
            if len(mapping_list) != len(selected_channels):
                error_msg = (
                    f"Error: Length mismatch between mapping_list ({len(mapping_list)}) "
                    f"and selected_channels ({len(selected_channels)}). "
                    f"Mapping channels: {mapping_list}, Selected channels: {selected_channels}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 按映射表调整通道顺序，去除多余的通道
            raw.reorder_channels(mapping_list)

            # 修改通道名
            dic = {}
            for i in range(len(mapping_list)):
                dic[mapping_list[i]] = selected_channels[i]
            raw.rename_channels(dic)
            # raw.pick(picks=selected_channels)  # 会改变raw的通道，且通道名称会按list的指定顺序排列

            # 导出规范化后的.edf文件
            raw.export(edf_path, overwrite=True)

            _, times = raw[:]
            raw_info = dict(sfreq=raw.info['sfreq'],
                            time=len(times) / raw.info['sfreq'],
                            valid_channels=','.join(raw.info['ch_names']))
            return raw_info
        except Exception as e:
            logger.error(f'Invalid .edf! Error info: {str(e)}')
            try:
                remove(edf_path)
                logger.info(f'Removed invalid .edf: {edf_path}')
            except Exception as remove_error:
                logger.error(f'Failed to remove invalid .edf: {edf_path}. Error info: {str(remove_error)}')
            raise e

    @classmethod
    def get_montage(cls):
        """
        获取绘制TPM所需的montage
        """
        xpos = [-0.0293387312092767, -0.0768097954926838, -0.051775707348028, -0.0949421285668141, -0.0683372810321719,
                -0.0768097954926838, -0.051775707348028,
                4.18445162392412E-18, -0.0293387312092767, 0.0293387312092767, 0.051775707348028, 0.0768097954926838,
                0.0683372810321719, 0.0949421285668141,
                0.051775707348028, 0.0768097954926838, 0.0293387312092767, 4.18445162392412E-18, 0]

        ypos = [0.0902953300444008, 0.0558055829928292, 0.0639376737816708, 0, 0, -0.0558055829928292,
                -0.0639376737816708,
                -0.0683372810321719,
                -0.0902953300444008, -0.0902953300444008, -0.0639376737816708, -0.0558055829928292, 0, 0,
                0.0639376737816708,
                0.0558055829928292, 0.0902953300444008, 0.0683372810321719, 0]

        zpos = [-0.00331545218673759, -0.00331545218673759, 0.0475, -0.00331545218673759, 0.0659925451936047,
                -0.00331545218673759, 0.0475, 0.0659925451936047,
                -0.00331545218673759, -0.00331545218673759, 0.0475, -0.00331545218673759, 0.0659925451936047,
                -0.00331545218673759, 0.0475, -0.00331545218673759,
                -0.00331545218673759, 0.0659925451936047, 0.095]

        position = {}
        for i in range(19):
            ch_name = EAVizConfig.channels_TPM[i]
            pos = [xpos[i], ypos[i], zpos[i]]
            position[ch_name] = array(pos)
        montage = channels.make_dig_montage(ch_pos=position)
        return montage
