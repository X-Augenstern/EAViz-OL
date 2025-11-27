# path
weightdata = "./SpiD/save_48.pth"  # Config函数中
tempdata = './SpiD/liangC3_ave.fif'  # finna3函数中

# model

model = 'Unet34'  # 正常使用 model(n) 为进行可视化时使用  net 和 Unet34 可以直接调用  net u3p带多尺度融合/Unet34 没有cat 直接Encoder D

model1 = 'SpikeRegressor'
model2 = 'SpikeRegressor'
loss_weight = 0.6
assert model in ['SpikeRegressor', 'Unet3Plus', 'Unet34']  # 支持多任务的是 net Unet34
# 功能选项--------------------------------------------------------
channelMethod = 'SA'  # 选项 'SA' 'mean' 'max' 'abssum' ‘None’   必要的调整选项
channel_number = 'Multi'  # Single 选定SQNN、画图时也可用
channel = 19  # U3P preparemodel 选定参数  channel_Method 选择None 时，U3P初始化的input channel 为 8 net none 的ch=19

assert channel_number in ['Single', 'Multi']
# p_ch_dict = {'谌嘉诚': 12, '方铭泽': 13, '孙弘浩': 13, '徐子宜': 4, '叶梦琪': 7, '易可欣': 12, '陈羽文': 12,
#              '陈修泽': 12, '吴配瑶': 12}  # ？？这个棘波检测对应的选择通道的不同吗？？选择的通道分别是12，13，13，4，......

# 测试使用 选取模型已保存的权重---------------------------------------

if model == 'SpikeRegressor':
    testweight = 'result_SpikeRegressor0/weights/save_100.pth'  #
    channel_number = 'Single'
    channelMethod = 'None'
    channel = 1
    SA = False

if model == 'Unet34':  # 这说明Unet34模型对应两个channelMethod
    if channelMethod == 'SA':
        channel = 1
        SA = True
        testweight = weightdata
    elif channelMethod == 'None':
        SA = False
        channel = 19
        testweight = 'result_19channels_Unet34_None1/weights/save_16.pth'

# 绘图的多个model载入---------------------------------------------------------------

elif model2 == 'SpikeRegressor':
    testweight2 = 'save_100.pth'

# 对于19个通道，每个通道的均值和方差
mean = [0.0011932824351784102, 0.0011390994131762048, 0.002174121577085201, 0.002013172372939422,
        -0.0009785268050904008,
        0.0002514346867206353, 0.0015363378885672504, -0.00253867868545743, -0.0025817066801644335,
        -0.0011758238115930847,
        0.0009989625724854227, 0.002661656853050991, -0.0015852695649372956, -0.0005333712131520023,
        -6.464343351495097e-05,
        0.0011752747863873576, 0.002279519405149002, 0.003212242891248821, -0.003328868490592702]
std = [31.649422589030447, 33.41086614793433, 31.072790936903637, 30.325820468923087, 26.89389439146389,
       28.20901495542336, 28.052230055440464, 25.847229627152533, 31.018606893590956, 31.315137397126133,
       26.68113085331614, 24.673989932452198, 31.562467510679348, 26.17375310899985, 30.13404382066629,
       28.180303034702355, 36.66892740731378, 32.64965539572045, 30.10440133194577]
