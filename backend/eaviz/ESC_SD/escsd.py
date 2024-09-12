from eaviz.ESC_SD.ESC.offline_process import *
from eaviz.ESC_SD.ESC.plot_result import plot_seid_res

STFT_adr = 'C:\\Users\\hp\\STFT.png'


class ESCSD:
    """
    ESC+SD分析类
    """

    @classmethod
    def sd(cls, raw, model, start_time):
        raw.load_data()
        raw, pre_margin = crop_tactic(raw, start_time, 4)

        # 预处理
        raw = raw.notch_filter(freqs=50)
        raw = raw.filter(l_freq=1, h_freq=70)
        # print(raw.times[-1])

        # 切片2
        raw = raw.crop(pre_margin, pre_margin + 4 - 1 / raw.info['sfreq'])
        # print(pre_margin)
        # print(pre_margin + 4 - 1 / raw.info['sfreq'])

        # tmp3
        tmp3, power, data = get_stft_feature(raw, STFT_adr)

        # tmp1
        tmp1 = data.transpose((1, 0))
        tmp1 = tensor(tmp1.astype('float32'))
        tmp1 = tmp1.reshape(1, 4000, 21)

        out1, out2, feature_map = model(tmp1, tmp3)

        # tmp1 = torch.randn(8, 4000, 21)
        # tmp3 = torch.randn(8, 3, 21, 32, 32)

        # feature map
        layer_label = ['input', 'conv1', 'block1', 'block2', 'block3', 'block4']
        feature_map.insert(0, tmp3)
        plot_feature_map(layer_label, feature_map)
        # (1, 3, 21, 32, 32)
        # (1, 16, 21, 16, 16)
        # (1, 16, 21, 9, 9)
        # (1, 32, 11, 5, 5)
        # (1, 64, 6, 3, 3)
        # (1, 128, 3, 2, 2)

        # (21, 32, 32, 3)
        # (21, 16, 16, 16)
        # (21, 9, 9, 16)
        # (11, 5, 5, 32)
        # (6, 3, 3, 64)
        # (3, 2, 2, 128)

        # feature
        plot_feature(power[2])
        # print('resnet:', out1.shape)
        # print('resnet:', out2.shape)
        # result
        plot_seid_res(out1, out2)

        # p = sum(map(lambda p: p.numel(), model.parameters()))
        # print('parameters size:', p)
        # device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # net = model.to(device)
        # summary(net, input_size=[(4000, 21),(3, 21, 256,256),(3, 256, 256)])

    # def esa(self):
    #     model = R3DClassifier(8, (2, 2, 2, 2), pretrained=True)
    #     checkpoint = load(AddressConfig.get_esa_adr('cp'), map_location=lambda storage, loc: storage)
    #     model.load_state_dict(checkpoint['state_dict'])
    #     model.eval()
    #
    #     # 预处理
    #     raw = self.raw.notch_filter(freqs=50)
    #     raw = raw.filter(l_freq=1, h_freq=70)
    #
    #     # 切片2
    #     raw = raw.crop(self.pre_margin, self.pre_margin + 4 - 1 / raw.info['sfreq'])
    #
    #     stft_buffer, power, _ = get_stft_feature(raw, AddressConfig.get_esa_adr('STFT'), save=False)
    #     out, feature_map = model(stft_buffer)
    #
    #     # feature map
    #     layer_label = ['input', 'conv1', 'conv2', 'conv3', 'conv4', 'conv5']
    #     feature_map.insert(0, stft_buffer)
    #     plot_feature_map(layer_label, feature_map, self.fm_signal)
    #
    #     # feature
    #     plot_feature(power[2], self.feature_signal)  # 只取索引为2用于绘图
    #
    #     # result
    #     plot_esa_res(out, self.res_signal)


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
