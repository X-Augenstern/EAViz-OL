from torch import from_numpy, stack


def dataset(data):
    # 对data做z-score标准化后转换为Tensor并还原回原始维度
    s_data_list = []
    for t in range(data.shape[0]):
        slice_data = data[t]  # 提取时间点 t 的二维子数组  (10,1000)
        processed_data = norm(slice_data)  # 调用 norm 函数处理二维子数组
        s_data_list.append(from_numpy(processed_data))  # 将处理后的数据添加到列表中 Tensor
    s_data = stack(s_data_list)  # 在第一维度对list内的张量进行堆叠 二—>三维 (11,10,1000)
    return s_data


def norm(slice_data):
    mean = [-0.019813645741049712, -0.08832978649691134, -0.17852094982207156, -0.141283147662929,
            -0.164364199798768, -0.10493702302254725, 0.0069039257850445224, 0.053706128833827776,
            -0.07108375609375886, -0.036934718124703704]
    std = [51.59277790417314, 55.41723123794839, 71.50782941925381, 67.58345657953764, 55.94475895317833,
           52.58134875167906, 28.773163340067427, 28.172769340175684, 25.5494790918186, 24.69622808553754]

    # z-score标准化
    for i in range(slice_data.shape[0]):
        slice_data[i] = (slice_data[i] - mean[i]) / std[i]
    return slice_data
