from os import makedirs, path
from shutil import rmtree
from matplotlib.pyplot import savefig, close
from mne import Annotations, read_evokeds
from numpy import corrcoef
from config.env import EAVizConfig
from eaviz.SpiD.Premodel import getlabel
from eaviz.SpiD.edf2mat import filter_2sIIR, edf2mat, anno_txt
from eaviz.SpiD.finnal3 import get_label_data
from eaviz.SpiD.mat2npz import mat2npz
from utils.edf_util import EdfUtil


class SPID:
    """
    SpiD分析类
    """

    @staticmethod
    def tm(raw, start_time, stop_time, auto=False):
        raw.load_data()

        # 滤波
        raw_filtered = EdfUtil.normal_filter(raw)

        # 清除annotations
        raw_filtered.set_annotations(Annotations([], [], []))

        # 加载模板数据
        template = read_evokeds(EAVizConfig.AddressConfig.get_spid_adr('tem'), verbose='error')[0]
        template_data = template.data  # (19,150)

        # 初始化保存相关窗口的列表
        corr_windows = []

        # calculate SWI
        total_dur = 0

        # 滑动窗口匹配，窗口大小为 0.3 秒，步长为 0.01 秒
        for i in range(int(start_time) * 500, int(stop_time) * 500 - 150, 5):
            # 获取当前窗口内的数据
            window_data = raw_filtered.get_data(start=i, stop=i + 150)  # (19,150)
            # 计算当前窗口内的相关度
            corr = corrcoef(window_data, template_data)[0, 1]  # (19,150) 取[0,1]作为参考，不取[0,0]是因为对角线（变量自身与自身）的相关系数都是1
            abs_corr = abs(corr)  # 正相关和负相关都可以
            # 判断相关度是否超过阈值，如果超过则保存当前窗口的起始和终止时间
            if abs_corr > EAVizConfig.SpiDConfig.CORR_THRESHOLD:
                corr_windows.append((i / 500, (i + 150) / 500))

        annotations_list = []
        if len(corr_windows) > 0:
            for start, end in get_label_data(corr_windows):
                dur = end - start
                raw_filtered.annotations.append(start, dur, '')
                total_dur += dur

                if auto:
                    annotations_list.append([start, end - start, 'SSW'])

        duration = stop_time - start_time
        swi = ('%.2f' % (total_dur / duration))

        plot_eeg_and_save(duration, start_time, raw_filtered, 15, 300e-6)
        return swi

    @staticmethod
    def ss(raw, model, start_time, stop_time, auto=False):
        raw.load_data()

        # todo 50 Notch
        raw1 = raw.notch_filter(freqs=50)

        # 用于绘制
        raw_filtered = raw1.copy().filter(l_freq=1, h_freq=70)  # filter直接修改了原始对象，需要先copy

        # 切片
        sfreq = raw1.info['sfreq']
        raw1 = raw1.crop(start_time, stop_time - 1 / sfreq)
        record_microvolts = raw1.get_data() * 1e6  # 单位转换

        # 0.5-50 BP
        passband = [0.5, 50]  # passband for bandpass filter
        forder = 6  # filter order
        record1 = filter_2sIIR(record_microvolts, passband, EAVizConfig.SpiDConfig.SAMPLE_RATE, forder, 'bandpass')

        # folder process
        mat_path = EAVizConfig.AddressConfig.get_spid_adr('mat')
        npz_path = EAVizConfig.AddressConfig.get_spid_adr('npz')
        SPID.clean_folder_list([mat_path, npz_path])
        # 如果这个目录或其任何父目录不存在的话，创建一个名为 mat_path 的目录。
        # 如果这个目录已经存在，代码不会有任何错误，而是正常继续执行。这在确保创建目录时不因目录已存在而中断程序执行的情况下非常有用。
        makedirs(mat_path, exist_ok=True)
        makedirs(npz_path, exist_ok=True)

        # edf2mat
        edf2mat(record1, mat_path)

        # 生成伪标签以满足数据格式条件
        anno_txt(mat_path, record1.shape[1], sfreq)  # record1.shape[1] = raw.n_times

        # mat2npz
        mat2npz(mat_path, npz_path)

        # calculate SWI
        total_dur = 0

        raw_filtered.set_annotations(Annotations([], [], []))

        # 得到npz后
        annotations_list = []
        res = getlabel(model, npz_path)
        if len(res) > 0:
            for start, end in res:
                real_dur = (end - start) / sfreq
                real_start = start / sfreq + start_time
                raw_filtered.annotations.append(real_start, real_dur, '')
                total_dur += real_dur

                if auto:
                    annotations_list.append([real_start, real_dur, 'SSW'])

        duration = stop_time - start_time
        swi = '%.2f' % (total_dur / duration)

        plot_eeg_and_save(duration, start_time, raw_filtered, 15, 300e-6)
        return swi

    @staticmethod
    def clean_folder_list(folder_path_list):
        for p in folder_path_list:
            if path.exists(p):
                rmtree(p)


def plot_eeg_and_save(duration, start_time, raw, dur_th, scaling):
    text_size = 16
    font_family = "Microsoft YaHei"
    if raw.annotations:
        if duration >= dur_th:
            eeg_plot = raw.plot(duration=duration, show=False, scalings=scaling, start=start_time,
                                show_scrollbars=False)
            raw.annotations.rename(mapping={'': 'SSW'})
            # Add SSW
            fig = eeg_plot.get_figure()
            fig.suptitle('SSW', fontsize=text_size, fontweight='bold', color='#1f77b4', y=0.98)
        else:
            raw.annotations.rename(mapping={'': 'SSW'})
            eeg_plot = raw.plot(duration=duration, show=False, scalings=scaling, start=start_time,
                                show_scrollbars=False)
        # Add legend
        event_label = "SSW: Spike-slow wave"
        # 获取了绘图的第一个轴（Axes）对象并设置图例
        eeg_plot.get_axes()[0].legend([event_label], loc='lower center', bbox_to_anchor=(0.44, -0.18),
                                      frameon=False, prop={'family': font_family, 'size': text_size})
    else:
        eeg_plot = raw.plot(duration=duration, show=False, scalings=scaling, start=start_time,
                            show_scrollbars=False)

    # 获取第一个轴对象，通常包含图表的标题和注释
    ax = eeg_plot.mne.ax_main
    # 设置横轴label字体
    ax.set_xlabel(ax.get_xlabel(), fontproperties=font_family, fontsize=text_size)
    # 统一设置坐标轴刻度字体大小和颜色
    # ax.tick_params(axis='both', which='major', labelsize=text_size, labelcolor=ThemeColorConfig.get_txt_color())
    ax.tick_params(axis='both', which='major', labelsize=text_size)
    # 遍历这个轴上的所有文本对象，设置字体
    for text in ax.texts:
        text.set_weight('bold')
        text.set_fontsize(text_size)

    # Save the figure
    eeg_plot.tight_layout()
    savefig(EAVizConfig.AddressConfig.get_spid_adr('res'), format='png', dpi=600)
    close()
