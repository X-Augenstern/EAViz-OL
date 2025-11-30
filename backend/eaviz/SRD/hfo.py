from torch import device, cuda, from_numpy, max, float32, no_grad
from numpy import array, mean, std
from mne import Annotations

use_device = device("cuda" if cuda.is_available() else "cpu")


def preprocess(raw, start_time, stop_time):
    raw.notch_filter(freqs=50)

    t_idx = raw.time_as_index([start_time, stop_time])  # 将时间值转换为对应的数据索引 ndarray [5000, 10000]
    data, _ = raw[:, t_idx[0]:t_idx[1]]  # 从原始数据中提取指定时间段内的数据 (1,5000)
    data = data * 1e6
    sliced_data = []  # 99*(1,100)
    start_idx = 0
    while start_idx + 100 <= data.shape[1]:  # 0-100 50-150 ... 4900-5000: 99段 ——> 1段（0.1s） ——> 0-0.1 0.05-0.15 ...
        slice_data = data[:, start_idx:start_idx + 100]  # (1,100)
        sliced_data.append(slice_data)
        start_idx += 50  # 滑动窗口
    sliced_data = array(sliced_data)
    return raw, sliced_data  # (99,1,100)


def predicted(model, preprocessed_data):
    input_data = from_numpy(preprocessed_data).to(use_device)  # (99,1,100)
    num_samples = input_data.size(0)  # 99
    ones_indices = []  # 存储预测结果为1的序列号
    batch_size = 32
    for i in range(0, num_samples, batch_size):
        batch = input_data[i:i + batch_size]  # 获取当前小批量数据 (32,1,100)

        if i + batch_size > num_samples:
            # 处理最后一个不满 32 的批次
            remaining_samples = num_samples - i
            batch = input_data[i:i + remaining_samples]

        with no_grad():
            batch = batch.type(float32)
            output = model(batch)  # (32,2) remain(3,2)
            _, predicted_labels = max(output, 1)  # (32,) (3,)
            # 记录预测结果为1和0的序列号
            for j, label in enumerate(predicted_labels):
                if label == 1:
                    ones_indices.append(i + j)
    # print(ones_indices)
    return ones_indices


def merged(raw, predicted_data, start_time):
    intervals = [(0.05 * n + start_time, 0.05 * n + 0.1 + start_time) for n in predicted_data]
    merged_data = []
    for start, end in intervals:
        if not merged_data or merged_data[-1][1] < start:
            merged_data.append([start, end])
        else:
            merged_data[-1][1] = end

    descriptions = ['HFO'] * len(merged_data)
    onsets = [item[0] for item in merged_data]
    durations = [item[1] - item[0] for item in merged_data]
    raw.set_annotations(Annotations(onsets, durations, descriptions))
    return raw


def get_bias(high_data):
    mean_val = mean(high_data)
    std_val = std(high_data)
    return mean_val - std_val * 2, mean_val + std_val * 2
