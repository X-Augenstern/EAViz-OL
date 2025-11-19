from torch import from_numpy
from numpy import array
from eaviz.AD import setdata
from eaviz.AD.APSD import APSD
from eaviz.AD.gogogo import Art_Dec
from utils.edf_util import EdfUtil


class AD:
    """
    AD分析类
    """

    @staticmethod
    def ad(raw, start_time, fb_idx, arti_list, mod1, mod2, mod2_name):
        raw.load_data()

        # 滤波
        raw_filtered = EdfUtil.normal_filter(raw)

        # channels = ['Fp1', 'Fp2', 'F7', 'F8', 'T3', 'T4', 'T5', 'T6', 'O1', 'O2']
        selected_indices = [0, 1, 10, 11, 12, 13, 14, 15, 8, 9]

        s_freq = int(raw_filtered.info['sfreq'])
        time = int(raw_filtered.n_times / s_freq)  # 1200 int 向下取整

        raw_data = raw_filtered.get_data()  # (19,1200000) 1200s
        # re_data = raw_data.reshape(time, 19, s_freq)  # (1200,19,1000) (总时长,通道数,采样频率)

        three_dim_array = []
        for i in range(time):
            start_index = i * 1000  # 计算起始索引
            end_index = (i + 1) * 1000  # 计算结束索引
            data_to_add = raw_data[:, start_index:end_index]
            three_dim_array.append(data_to_add)

        re_data = array(three_dim_array)

        stop_time = start_time + 11
        Hdl_Var = re_data[start_time:stop_time]  # (11,19,1000)
        s_data = (Hdl_Var[:, selected_indices, :] * 1000000)  # (11,10,1000)
        X = setdata.dataset(s_data)  # (11,10,1000)

        n_data = from_numpy(raw_data)

        APSD(n_data, start_time, stop_time, fb_idx)  # toposize
        annotations_list, des_list = Art_Dec(X, arti_list, raw_filtered, start_time, mod1, mod2, mod2_name)
