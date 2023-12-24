import matplotlib.pyplot as plt
import numpy as np
import os

cur_root = os.path.dirname(os.path.abspath(__file__))

# 数据
benchmarks = ["BasicMath benchmark", "Dijkstra benchmark", "Qsort benchmark", "Bitcount benchmark", "Patricia benchmark"]
lab_params = ["inorder\nL1=32K\nL2=512K", "inorder\nL1=64K\nL2=1M", "outoforder\nL1=32K\nL2=512K", "outoforder\nL1=64K\nL2=1M"]
architectures = ["ARM", "X86"]

def read_data(file_path):
    fp = open(file_path, mode='r')
    lines = fp.readlines()
    fp.close()

    metrics = np.random.randn(4, len(benchmarks), len(architectures), len(lab_params))
    # metrics = [np.random.randn(len(benchmarks), len(architectures), len(lab_params))]*4

    benchmark2idx = {'basicmath':0, 'dijkstra':1, 'qsort':2, 'bitcnts':3, 'patricia':4 }
    isa2idx = {'x86':0, 'arm':1}

    # metric = np.random.randn(len(benchmarks), len(architectures), len(lab_params))
    for i in range(len(lines)):
        if lines[i].startswith('benchmark'):
            benchmark_idx = benchmark2idx[lines[i].rstrip('\n').split('=')[-1]]
            i+=1
            isa_idx = isa2idx[lines[i].rstrip('\n').split('=')[-1]]
            i+=1
            lab_idx = -1
            if lines[i].rstrip('\n') == 'cpu-type=inorder, L1=32kB, L2=512kB':
                lab_idx = 0
            elif lines[i].rstrip('\n') == 'cpu-type=inorder, L1=64kB, L2=1MB':
                lab_idx = 1
            elif lines[i].rstrip('\n') == 'cpu-type=outoforder, L1=32kB, L2=512kB':
                lab_idx = 2
            elif lines[i].rstrip('\n') == 'cpu-type=outoforder, L1=64kB, L2=1MB':
                lab_idx = 3
            i+=1
            # 读取四个指标
            for j in range(4):
                metrics[j][benchmark_idx][isa_idx][lab_idx] = float(lines[i+j].rstrip('\n').split('=')[-1])
            i+=4
    return metrics

def draw(metric, metric_name):
    nrow = 2
    ncol = 3
    # 设置图形大小
    fig, axes = plt.subplots(nrows=nrow, ncols=ncol, figsize=(13, 7))
    plt.subplots_adjust(hspace=0.5)
    for i, ax in enumerate(axes.flat):
        if i == nrow * ncol-1:
            ax.axis('off')
            break
        x86_value = metric[i][0]
        arm_value = metric[i][1]

        x = np.arange(len(lab_params))  # the label locations
        width = 0.3  # the width of the bars

        rects1 = ax.bar(x - width/2, arm_value, width, label='ARM')
        rects2 = ax.bar(x + width/2, x86_value, width, label='X86')

        ax.set_ylabel(metric_name)
        ax.set_title(benchmarks[i])
        ax.set_xticks(x)
        ax.set_xticklabels(lab_params)
        ax.legend()

    manager = plt.get_current_fig_manager()
    manager.full_screen_toggle()
    # 调整布局
    plt.tight_layout()
    plt.savefig(os.path.join(cur_root, f'metrics_chart/{metric_name if not metric_name.startswith("throughput") else "throughput"}.png'))
    

if __name__ == '__main__':
    file_path = os.path.join(cur_root, 'sim_result.txt')
    metrics = read_data(file_path)
    idx2metricname = {0:'average cpi', 1:'L2 cache miss rate', 2: 'total energy(mJ)', 3:'throughput(KB\s)'}
    for i in range(len(metrics)):
        draw(metrics[i], idx2metricname[i])
    
    # plt.show()