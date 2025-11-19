from torch import tensor
from eaviz.ESC_SD.offline_process import *
from eaviz.ESC_SD.plot_result import plot_sd_res, plot_esc_res
from utils.edf_util import EdfUtil


class ESCSD:
    """
    ESC+SD分析类
    """

    @staticmethod
    def preprocess(raw, start_time):
        raw.load_data()
        raw, pre_margin = crop_tactic(raw, start_time, 4)

        # 预处理
        raw = EdfUtil.normal_filter(raw)

        # 切片2
        raw = raw.crop(pre_margin, pre_margin + 4 - 1 / raw.info['sfreq'])
        return raw

    @classmethod
    def esc(cls, raw, model, start_time):
        raw = cls.preprocess(raw, start_time)

        stft_buffer, power, _ = get_stft_feature(raw)
        out, feature_map = model(stft_buffer)

        # feature map
        layer_label = ['input', 'conv1', 'conv2', 'conv3', 'conv4', 'conv5']
        feature_map.insert(0, stft_buffer)
        plot_feature_map('ESC', layer_label, feature_map)

        # feature
        plot_feature('ESC', power[2])  # 只取索引为2用于绘图

        # result
        plot_esc_res(out)

    @classmethod
    def sd(cls, raw, model, start_time):
        raw = cls.preprocess(raw, start_time)

        # tmp3
        tmp3, power, data = get_stft_feature(raw)

        # tmp1
        tmp1 = data.transpose((1, 0))
        tmp1 = tensor(tmp1.astype('float32'))
        tmp1 = tmp1.reshape(1, 4000, 21)

        out1, out2, feature_map = model(tmp1, tmp3)

        # feature map
        layer_label = ['input', 'conv1', 'block1', 'block2', 'block3', 'block4']
        feature_map.insert(0, tmp3)
        plot_feature_map('SD', layer_label, feature_map)

        # feature
        plot_feature('SD', power[2])
        plot_sd_res(out1, out2)


def crop_tactic(raw, start_time, dur):
    """
    Presuming the largest sfreq reaches 1000Hz, crop the raw with margin (+-4s).
    (Notch Filter length: 6601 samples (6.601 s))

    AD/SpiD requires to add resultant annotations to the raw, so this tactic seems not advisable.
    """
    margin = 4

    t_max = raw.times[-1]
    sfreq = raw.info['sfreq']

    stop_time = start_time + dur - 1 / sfreq
    if start_time - margin < 0:
        crop_start = 0
    else:
        crop_start = start_time - margin
    if stop_time + margin > t_max:
        crop_stop = t_max
    else:
        crop_stop = stop_time + margin
    raw.crop(tmin=crop_start, tmax=crop_stop)
    return raw, start_time - crop_start
