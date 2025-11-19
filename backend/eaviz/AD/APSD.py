from numpy import arange
from mpl_toolkits.mplot3d import Axes3D  # noqa
from mne import create_info, EvokedArray
from matplotlib.pyplot import savefig, close, gcf
from utils.edf_util import EdfUtil
from config.env import EAVizConfig


def APSD(data, tmin, tmax, fb_idx):  # size
    # 创建info对象
    info = create_info(ch_names=EAVizConfig.ChannelEnum.TPM.value, sfreq=1000., ch_types='eeg')
    # print(info)

    # 创建evokeds对象
    evoked = EvokedArray(data, info)
    if fb_idx != 0:
        freq_band = EAVizConfig.PSDEnum.FREQ_BANDS.value[fb_idx - 1]
        evoked.filter(freq_band[0], freq_band[1])

    # evokeds设置通道
    if tmax is None:
        times = tmin
    else:
        times = arange(tmin, tmax)  # size
    evoked.set_montage(EdfUtil.get_montage())

    text_size = 16

    tpm = evoked.plot_topomap(times, ch_type="eeg", show=False, nrows=3, ncols=4)
    fig = tpm if hasattr(tpm, 'axes') else gcf()

    # 放大子图标题及 color_bar 刻度
    for ax in fig.axes:
        if ax.get_title():
            ax.set_title(ax.get_title(), fontsize=text_size)

    # 放大 colorbar
    cbar_ax = fig.axes[-1]  # 通常最后一个axes是colorbar
    cbar_ax.tick_params(labelsize=text_size)

    savefig(EAVizConfig.AddressConfig.get_ad_adr('topo'), format='png', dpi=300)
    close()
