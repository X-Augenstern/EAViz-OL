from psutil import cpu_count, cpu_times_percent, virtual_memory, disk_usage, disk_partitions, Process
from utils.common_util import bytes2human
from platform import platform, node, machine, python_version as pfpy
from socket import gethostbyname, gethostname
from os import getpid, getcwd, path
from time import localtime, strftime, time
from module_admin.entity.vo.server_vo import *


class ServerService:
    """
    服务监控模块服务层
    """
    @staticmethod
    def get_server_monitor_info():
        """
        获取服务监控信息Service
        """
        # CPU信息
        cpu_num = cpu_count(logical=True)  # 获取逻辑CPU核心数
        cpu_usage_percent = cpu_times_percent()  # 获取CPU使用百分比
        cpu_used = cpu_usage_percent.user  # 获取用户态CPU使用率
        cpu_sys = cpu_usage_percent.system  # 获取系统态CPU使用率
        cpu_free = cpu_usage_percent.idle  # 空闲率
        cpu = CpuInfo(cpuNum=cpu_num, used=cpu_used, sys=cpu_sys, free=cpu_free)

        # 内存信息
        memory_info = virtual_memory()  # 获取内存使用情况
        memory_total = bytes2human(memory_info.total)
        memory_used = bytes2human(memory_info.used)
        memory_free = bytes2human(memory_info.free)
        memory_usage = memory_info.percent
        mem = MemoryInfo(total=memory_total, used=memory_used, free=memory_free, usage=memory_usage)

        # 主机信息
        hostname = gethostname()  # 获取主机名
        computer_ip = gethostbyname(hostname)  # 获取IP
        os_name = platform()  # 获取操作系统名称
        computer_name = node()  # 获取计算机名称
        os_arch = machine()  # 获取操作系统架构
        user_dir = path.abspath(getcwd())  # 获取当前用户目录
        sys = SysInfo(computerIp=computer_ip, computerName=computer_name, osArch=os_arch, osName=os_name,
                      userDir=user_dir)

        # python解释器信息
        current_pid = getpid()  # 获取当前进程id
        current_process = Process(current_pid)  # 获取当前进程信息
        python_name = current_process.name()  # 获取当前进程名字
        python_version = pfpy()  # 获取py版本
        python_home = current_process.exe()  # 获取当前 Python 进程的可执行文件路径
        start_time_stamp = current_process.create_time()  # 获取当前进程起始时间
        start_time = strftime("%Y-%m-%d %H:%M:%S", localtime(start_time_stamp))
        current_time_stamp = time()
        difference = current_time_stamp - start_time_stamp  # 获取当前进程运行时间
        # 将时间差转换为天、小时和分钟数
        days = int(difference // (24 * 60 * 60))  # 每天的秒数
        hours = int((difference % (24 * 60 * 60)) // (60 * 60))  # 每小时的秒数
        minutes = int((difference % (60 * 60)) // 60)  # 每分钟的秒数
        run_time = f"{days}天{hours}小时{minutes}分钟"
        pid = getpid()  # 获取当前Python程序的pid
        current_process_memory_info = Process(pid).memory_info()  # 获取该进程的内存信息
        py = PyInfo(
            name=python_name,
            version=python_version,
            startTime=start_time,
            runTime=run_time,
            home=python_home,
            total=bytes2human(memory_info.available),
            used=bytes2human(current_process_memory_info.rss),
            free=bytes2human(memory_info.available - current_process_memory_info.rss),
            usage=round((current_process_memory_info.rss / memory_info.available) * 100, 2)
        )

        # 磁盘信息
        io = disk_partitions()  # 获取系统中所有磁盘分区的信息
        sys_files = []
        for i in io:
            o = disk_usage(i.device)  # 获取该分区的使用情况 o 是一个 psutil._common.sdiskusage 对象，包含总空间、已用空间、剩余空间和使用率的信息
            disk_data = SysFiles(
                dirName=i.device,  # 分区的设备名称，例如 /dev/sda1
                sysTypeName=i.fstype,  # 分区的文件系统类型，例如 ext4、ntfs
                typeName="本地固定磁盘（" + i.mountpoint.replace('\\', '') + "）",  # 分区的挂载点名称，并标注为本地固定磁盘
                total=bytes2human(o.total),
                used=bytes2human(o.used),
                free=bytes2human(o.free),
                usage=f'{disk_usage(i.device).percent}%'
            )
            sys_files.append(disk_data)

        result = ServerMonitorModel(cpu=cpu, mem=mem, sys=sys, py=py, sysFiles=sys_files)

        return result
