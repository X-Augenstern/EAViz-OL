from json import dumps
from eaviz.SRD.hfo import preprocess, predicted, merged, get_bias


class SRD:
    """
    SRD分析类
    """

    @staticmethod
    def stream_srd_data(raw, model, start_time, stop_time, ch_idx, window_size=5.0):
        """
        流式输出 SRD 数据
        :param raw: MNE Raw 对象
        :param model: 预训练模型
        :param start_time: 开始时间（秒）
        :param stop_time: 结束时间（秒）
        :param ch_idx: 通道索引
        :param window_size: 窗口大小（秒），默认 5 秒
        :return: 生成器，每次 yield 一个窗口的数据
        """
        raw.pick(ch_idx)
        raw.load_data()
        raw.notch_filter(freqs=50)

        # 创建滤波后的副本
        raw_low = raw.copy().filter(l_freq=1, h_freq=70)
        raw_high = raw.copy().filter(l_freq=80, h_freq=450)

        # 处理整个时间段，生成 HFO 标注
        raw_notch, sliced_data = preprocess(raw, start_time, stop_time)
        predicted_indices = predicted(model, sliced_data)
        merged_raw = merged(raw_notch, predicted_indices, start_time)

        # 获取所有标注
        all_annotations = []
        for ann in merged_raw.annotations:
            all_annotations.append({
                'onset': float(ann['onset']),
                'duration': float(ann['duration']),
                'description': str(ann['description'])
            })

        # 首先发送所有标注的汇总信息，让前端可以先绘制标注区域
        summary = {
            'type': 'summary',
            'totalAnnotations': len(all_annotations),
            'annotations': all_annotations,
            'timeRange': {
                'start': float(start_time),
                'stop': float(stop_time)
            }
        }
        yield dumps(summary).encode('utf-8') + b'\n'

        # 按窗口流式输出数据
        cur_time = start_time
        sfreq = raw.info['sfreq']

        while cur_time < stop_time:
            window_end = min(cur_time + window_size, stop_time)

            # 获取时间索引
            t_idx = raw.time_as_index([cur_time, window_end])
            if t_idx[0] >= t_idx[1]:
                break

            # 提取三个数据流
            raw_data, raw_times = raw[:, t_idx[0]:t_idx[1]]
            low_data, low_times = raw_low[:, t_idx[0]:t_idx[1]]
            high_data, high_times = raw_high[:, t_idx[0]:t_idx[1]]

            # 转换为微伏
            raw_data = raw_data * 1e6
            low_data = low_data * 1e6
            high_data = high_data * 1e6

            # 计算 bias（使用当前窗口的高频数据）
            bias_lower, bias_upper = get_bias(high_data[0])

            # 准备窗口数据（不包含标注，标注已通过汇总信息发送）
            window_data = {
                'type': 'data',
                'time': cur_time,
                'windowSize': window_size,
                'sfreq': float(sfreq),
                'raw': {
                    'times': raw_times.tolist(),
                    'data': raw_data[0].tolist()
                },
                'low': {
                    'times': low_times.tolist(),
                    'data': low_data[0].tolist()
                },
                'high': {
                    'times': high_times.tolist(),
                    'data': high_data[0].tolist()
                },
                'bias': {
                    'lower': float(bias_lower),
                    'upper': float(bias_upper)
                }
            }

            # 将数据编码为 JSON 字符串，然后转换为字节
            json_str = dumps(window_data)
            yield json_str.encode('utf-8') + b'\n'  # 使用换行符分隔每个窗口

            cur_time = window_end
