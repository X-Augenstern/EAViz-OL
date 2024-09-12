from numpy import float32, concatenate, array
from torch.nn.functional import softmax
from matplotlib.pyplot import rcParams, close, figure, tight_layout, savefig, cla, bar, text, xticks, axvline, ylabel, \
    ylim, yticks
from io import BytesIO

rcParams['font.sans-serif'] = ['Microsoft YaHei']
rcParams['axes.unicode_minus'] = False


def plot_esa_res(data, res_signal):
    # 1
    # class_label = ['BECT', 'CAE', 'CSWS', 'EIEE', 'FS', 'Normal', 'WEST']
    # 19
    class_label = ['BECT', 'CAE', 'CSWS', 'EIEE', 'Else', 'FS', 'Normal', 'WEST']
    close()
    figure(figsize=(8, 6))
    _plot_probs([data], class_label)

    # idx = np.argmax(input.cpu().data.numpy())  # data:(1,7) 获取最大概率值索引

    tight_layout()
    buffer = BytesIO()
    savefig(buffer, format='png', dpi=300)
    buffer.seek(0)
    res_signal.emit(buffer.getvalue())
    cla()


def plot_seid_res(data1, data2):
    class_label = ['EIEE', 'WEST', 'CAE', 'FS+', 'BECT', 'CSWS', 'interictal', 'seizure']
    close()
    figure(figsize=(8, 6))
    _plot_probs([data1, data2], class_label, 5)

    tight_layout()
    buffer = BytesIO()
    savefig(buffer, format='png', dpi=300)
    savefig('./res.png', format='png', dpi=300)
    buffer.seek(0)
    # res_signal.emit(buffer.getvalue())
    print("plot_seid_res")
    cla()  # 会清除当前轴上的内容，包括图形。在调用 plt.cla() 后，图形就被清除了，导致保存时没有内容可保存，因此报错。


def _plot_probs(data, class_labels, v_idx=None):
    all_probs = array([])

    for i in range(len(data)):
        all_probs = concatenate((all_probs, softmax(data[i], dim=1).detach().numpy()[0]))  # softmax

    bar(class_labels, all_probs * 100, align='center', color='black', alpha=0.8)  # 直接将class_label作为x
    result = [("%.2f" % i) for i in all_probs * 100]
    for a, b in zip(class_labels, float32(result)):
        # x:a y:b+2 text:b
        text(a, b + 2, b, ha='center', va='bottom', fontproperties="Arial", fontsize=10, fontweight='bold')

    # 设置分隔线
    if v_idx is not None:
        xticks_positions = xticks()[0]
        mid = (xticks_positions[v_idx] + xticks_positions[v_idx + 1]) / 2
        axvline(mid, color='grey', linestyle='--', linewidth=2)

    ylabel('概率值(%)', fontproperties="Microsoft YaHei", fontsize=12, fontweight='bold')
    # plt.title('概率分布图', fontproperties="Microsoft YaHei", loc='left', fontsize=12, fontweight='bold')
    xticks(fontproperties="Arial", fontsize=11, fontweight='bold')
    yticks(fontproperties="Arial", fontsize=12, fontweight='bold')
    ylim([0, 100])
