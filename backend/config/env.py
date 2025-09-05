from os import path, getcwd, environ, makedirs
from sys import argv
from argparse import ArgumentParser
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from enum import Enum
from matplotlib.colors import TABLEAU_COLORS


class AppSettings(BaseSettings):
    """
    应用配置
    """
    app_env: str = 'dev'
    app_name: str = 'EAViz-OL'
    app_root_path: str = '/dev-api'  # 应用的代理路径
    app_host: str = '0.0.0.0'
    app_port: int = 9099
    app_version: str = '1.0.0'
    app_reload: bool = True
    app_ip_location_query: bool = True
    app_same_time_login: bool = True  # 能否同时登录


class JwtSettings(BaseSettings):
    """
    Jwt配置
    """
    jwt_secret_key: str = 'b01c66dc2c58dc6a0aabfe2144256be36226de378bf87f72c0c795dda67f4d55'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 1440  # 24h
    jwt_redis_expire_minutes: int = 30


class DataBaseSettings(BaseSettings):
    """
    数据库配置
    """
    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_username: str = 'root'
    db_password: str = '527644117'
    db_database: str = 'eaviz'
    db_echo: bool = True  # 打印出所有的数据库查询语句
    db_max_overflow: int = 10  # 连接池允许的最大连接数
    db_pool_size: int = 50  # 连接池的大小
    db_pool_recycle: int = 3600  # 连接多长时间后需要被回收，防止数据库连接长时间不关闭导致失效 s
    db_pool_timeout: int = 30  # 获取连接池的超时时间 s


class RedisSettings(BaseSettings):
    """
    Redis配置
    """
    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    redis_username: str = ''
    redis_password: str = '123456'
    redis_database: int = 2


class UploadSettings:
    """
    上传配置
    """
    # 在生成文件的 URL 时提供了一个前缀路径，这通常用于区分文件的存储位置和访问路径。
    # 例如，在 web 应用中，文件可能存储在服务器的某个目录中，但通过 HTTP 访问时，需要一个特定的路径前缀来路由请求到正确的文件位置。（比如头像）
    UPLOAD_PREFIX = '/profile'
    UPLOAD_PATH = 'EAViz Files/upload_path'
    UPLOAD_MACHINE = 'A'
    DEFAULT_ALLOWED_EXTENSION = [
        # 图片
        "bmp", "gif", "jpg", "jpeg", "png",
        # word excel powerpoint
        "doc", "docx", "xls", "xlsx", "ppt", "pptx", "html", "htm", "txt",
        # 压缩文件
        "rar", "zip", "gz", "bz2",
        # 视频格式
        "mp4", "avi", "rmvb",
        # pdf
        "pdf",
        # EDF文件
        "edf"
    ]
    DOWNLOAD_PREFIX = '/download'
    DOWNLOAD_PATH = 'EAViz Files/download_path'

    def __init__(self):
        if not path.exists(self.UPLOAD_PATH):
            makedirs(self.UPLOAD_PATH)
        if not path.exists(self.DOWNLOAD_PATH):
            makedirs(self.DOWNLOAD_PATH)


class CachePathConfig:
    """
    缓存目录配置
    """
    PATH = path.join(path.abspath(getcwd()), 'caches')  # 获取当前工作目录 \EAViz_OL\backend\config\caches
    PATHSTR = 'caches'


class RedisInitKeyConfig:
    """
    系统内置Redis键名
    """
    ACCESS_TOKEN = {'key': 'access_token',
                    'remark': '登录令牌信息'}  # full key：access_token:session_id/user_id | value：token
    SYS_DICT = {'key': 'sys_dict', 'remark': '数据字典'}
    SYS_CONFIG = {'key': 'sys_config', 'remark': '配置信息'}
    CAPTCHA_CODES = {'key': 'captcha_codes', 'remark': '图片验证码'}  # full key：captcha_codes:uuid | value：code
    ACCOUNT_LOCK = {'key': 'account_lock', 'remark': '用户锁定'}  # full key：account_lock:user_name | value：user_name
    # full key：password_error_count:user_name | value：password_error_counted
    PASSWORD_ERROR_COUNT = {'key': 'password_error_count', 'remark': '密码错误次数'}
    SMS_CODE = {'key': 'sms_code', 'remark': '短信验证码'}  # full key：sms_code:session_id | value：sms_code


class EAVizSettings:
    """
    EAViz配置
    """

    class ModelConfig:
        ESC_SD_model = ['', 'DSMN-ESS', 'R3DClassifier']
        AD_model = ['', 'Resnet34_AE_BCELoss', 'Resnet34_SkipAE_BCELoss', 'Resnet34_MemAE_BCELoss',
                    'Resnet34_VAE_BCELoss', 'SENet18_AE_BCELoss', 'SENet18_SkipAE_BCELoss',
                    'SENet18_MemAE_BCELoss', 'SENet18_VAE_BCELoss', 'VGG16_AE_BCELoss', 'VGG16_SkipAE_BCELoss',
                    'VGG16_MemAE_BCELoss', 'VGG16_VAE_BCELoss', 'DenseNet121_AE_BCELoss',
                    'DenseNet121_SkipAE_BCELoss', 'DenseNet121_MemAE_BCELoss', 'DenseNet121_VAE_BCELoss']
        SpiD_model = ['', 'Template Matching', 'Unet+ResNet34']
        SRD_model = ['', 'MKCNN']
        VD_model = ['', 'yolov5l_3dResnet']

        ESC_SD_model_des = 'This model requires the <INPUT> .EDF FILE:\n' \
                           'sfreq: 1000Hz\n' \
                           '21 channels, which can be selected in Select Signals Form per button ESC + SD (21 channels)\n' \
                           'preprocessing: None\n' \
                           'time span: 4s'
        AD_model_des = 'This model requires the <INPUT> .EDF FILE:\n' \
                       'sfreq: 1000Hz\n' \
                       '19 channels, which can be selected in Select Signals Form per button AD, SpiD (19 channels)\n' \
                       'preprocessing: None\n' \
                       'time span: 11s'
        SpiD_model_des = 'This model requires the <INPUT> .EDF FILE:\n' \
                         'sfreq: 500Hz\n' \
                         '19 channels, which can be selected in Select Signals Form per button AD, SpiD (19 channels)\n' \
                         'preprocessing: None\n' \
                         'time span: >=0.3s(Template) | multiple of 30s(Semantics)'
        SRD_model_des = 'This model requires the <INPUT> .EDF FILE:\n' \
                        'sfreq: 1000Hz\n' \
                        'preprocessing: None\n' \
                        'time span: >=1s'
        VD_model_des = 'This model requires the <INPUT> .MP4 FILE:\n' \
                       'frame per second: 20'

        @classmethod
        def get_des(cls, model):
            if model in cls.ESC_SD_model:
                return cls.ESC_SD_model_des
            elif model in cls.AD_model:
                return cls.AD_model_des
            elif model in cls.SpiD_model:
                return cls.SpiD_model_des
            elif model in cls.SRD_model:
                return cls.SRD_model_des
            elif model == 'VD':
                return cls.VD_model_des

    class ChannelEnum(Enum):
        """
        .name 获取枚举成员的名字，通过 .value 获取枚举成员的具体值
        """
        TPM = ['Fp1', 'F7', 'F3', 'T3', 'C3', 'T5', 'P3', 'Pz', 'O1', 'O2', 'P4', 'T6', 'C4', 'T4',
               'F4', 'F8', 'Fp2', 'Fz', 'Cz']  # 19
        CH21 = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7',
                'F8', 'T3', 'T4', 'T5', 'T6', 'A1', 'A2', 'Fz', 'Cz', 'Pz']  # 21 + A1、A2
        CH19 = ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2', 'F7', 'F8', 'T3', 'T4',
                'T5', 'T6', 'Fz', 'Cz', 'Pz']  # 19
        COLLECTED = ['Fp1', 'F7', 'F3', 'T3', 'C3', 'T5', 'P3', 'O1', 'Fp2', 'F8', 'F4', 'T4', 'C4', 'T6', 'P4',
                     'O2', 'Fz', 'Cz', 'Pz', 'A1', 'A2']  # 21

    class PSDEnum(Enum):
        COLORS = list(TABLEAU_COLORS.values())  # 获取颜色列表
        FREQ_LABELS = ["Delta", "Theta", "Alpha", "Beta", "Gamma"]
        FREQ_BANDS = [(0, 4), (4, 8), (8, 12), (12, 30), (30, 45)]

    class MontageEnum(Enum):
        XPOS = [-0.0293387312092767, -0.0768097954926838, -0.051775707348028, -0.0949421285668141, -0.0683372810321719,
                -0.0768097954926838, -0.051775707348028,
                4.18445162392412E-18, -0.0293387312092767, 0.0293387312092767, 0.051775707348028, 0.0768097954926838,
                0.0683372810321719, 0.0949421285668141,
                0.051775707348028, 0.0768097954926838, 0.0293387312092767, 4.18445162392412E-18, 0]

        YPOS = [0.0902953300444008, 0.0558055829928292, 0.0639376737816708, 0, 0, -0.0558055829928292,
                -0.0639376737816708,
                -0.0683372810321719,
                -0.0902953300444008, -0.0902953300444008, -0.0639376737816708, -0.0558055829928292, 0, 0,
                0.0639376737816708,
                0.0558055829928292, 0.0902953300444008, 0.0683372810321719, 0]

        ZPOS = [-0.00331545218673759, -0.00331545218673759, 0.0475, -0.00331545218673759, 0.0659925451936047,
                -0.00331545218673759, 0.0475, 0.0659925451936047,
                -0.00331545218673759, -0.00331545218673759, 0.0475, -0.00331545218673759, 0.0659925451936047,
                -0.00331545218673759, 0.0475, -0.00331545218673759,
                -0.00331545218673759, 0.0659925451936047, 0.095]

        BRAIN_REGIONS = {
            "中央区": ["C3", "C4", "Cz"],
            "枕区": ["T5", "T6", "O1", "O2"],
            "顶区": ["P3", "P4", "Pz"],
            "颞区": ["F7", "F8", "T3", "T4"],
            "额区": ["Fp1", "Fp2", "F3", "F4", "Fz"]
        }

    class AddressConfig:
        BASE_ROOT = UploadSettings.DOWNLOAD_PATH
        BASE_CP_ROOT = 'eaviz'
        CP_ITEM_NAME = ['ESC', 'SD', 'SRD', 'VD']
        FOLDER = {
            "ESC_SD/ESC": ["feature_map", "stft_feature", "res"],
            "ESC_SD/SD": ["feature_map", "stft_feature", "res"],
            "AD": ["index", "topomap", "res"],
            "SpiD": ["index", "family", "res", "mat", "npz"],
            "SRD": [],
            "VD": []
        }

        @classmethod
        def setup(cls):
            for module, subdirs in cls.FOLDER.items():
                base_path = path.join(cls.BASE_ROOT, module)
                makedirs(base_path, exist_ok=True)
                for sub in subdirs:
                    makedirs(path.join(base_path, sub), exist_ok=True)

            if not path.exists(cls.BASE_CP_ROOT):
                raise FileNotFoundError(
                    f"⚠️ 模型权重目录缺失: {cls.BASE_CP_ROOT} ，请手动放置权重文件。"
                )

        @classmethod
        def get_esc_adr(cls, name):
            base = path.join(cls.BASE_ROOT, "ESC_SD", "ESC")
            hashtable = {
                'fm': path.join(base, "feature_map", "feature_map.png"),
                'stft': path.join(base, "stft_feature", "stft_feature.png"),
                'res': path.join(base, "res", "res.png"),
            }
            return path.abspath(hashtable.get(name, ''))

        @classmethod
        def get_sd_adr(cls, name):
            base = path.join(cls.BASE_ROOT, "ESC_SD", "SD")
            hashtable = {
                'fm': path.join(base, "feature_map", "feature_map.png"),
                'stft': path.join(base, "stft_feature", "stft_feature.png"),
                'res': path.join(base, "res", "res.png"),
            }
            return path.abspath(hashtable.get(name, ''))

        @classmethod
        def get_ad_adr(cls, name, model_name=None):
            base = path.join(cls.BASE_ROOT, "AD")
            hashtable = {
                'idx': path.join(base, "index", f"{model_name}_light.html"),
                'topo': path.join(base, "topomap", "topomap.png"),
                'res': path.join(base, "res", "res.png")
            }
            return path.abspath(hashtable.get(name, ''))

        @classmethod
        def get_spid_adr(cls, name):
            base = path.join(cls.BASE_ROOT, "SpiD")
            hashtable = {
                'idx': path.join(base, "index", "idx_light.html"),
                'fam': path.join(base, "family", "fam_light.png"),
                'res': path.join(base, "res", "res.png"),
                'mat': path.join(base, "mat"),
                'npz': path.join(base, "npz")
            }
            return path.abspath(hashtable.get(name, ''))

        @classmethod
        def get_cp_adr(cls, name):
            base = path.join(cls.BASE_CP_ROOT)
            hashtable = {
                'ESC': path.join(base, "ESC_SD", "ESC", "A3D-EEG_epoch-19.pth.tar"),
                'SD': path.join(base, "ESC_SD", "SD", "0.15-EEG_epoch-19.pth.tar"),
                'SRD': path.join(base, "SRD", "model_weights.pth"),
                'VD': {
                    'cp1': path.join(base, "VD", "yolov5l_best.pt"),
                    'cp2': path.join(base, "VD", "3d_Resnet_best.pth")
                }
            }
            value = hashtable.get(name, '')
            if isinstance(value, dict):
                return {k: path.abspath(v) for k, v in value.items()}
            return path.abspath(value) if value else ''

        # # upload/2024/07/05
        # relative_path = (f'upload/'
        #                  f'{datetime.now().strftime("%Y")}/'
        #                  f'{datetime.now().strftime("%m")}/'
        #                  f'{datetime.now().strftime("%d")}')
        # # files/upload_path/upload/2024/07/05
        # dir_path = path.join(UploadConfig.UPLOAD_PATH, relative_path)
        # try:
        #     makedirs(dir_path)
        # except FileExistsError:
        #     pass
        # # demo_edf_20240705132949A605.edf
        # filename = (f'{file.filename.rsplit(".", 1)[0]}_'
        #             f'{datetime.now().strftime("%Y%m%d%H%M%S")}'
        #             f'{UploadConfig.UPLOAD_MACHINE}'
        #             f'{UploadUtil.generate_random_number()}.'
        #             f'{file.filename.rsplit(".")[-1]}')
        # # files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf
        # filepath = path.join(dir_path, filename)


class GetConfig:
    """
    获取配置
    """

    def __init__(self):
        self.parse_cli_args()

    @lru_cache()
    def get_app_config(self):
        """
        获取应用配置
        """
        # 实例化应用配置模型
        return AppSettings()

    @lru_cache()
    def get_jwt_config(self):
        """
        获取Jwt配置
        """
        # 实例化Jwt配置模型
        return JwtSettings()

    @lru_cache()
    def get_database_config(self):
        """
        获取数据库配置
        """
        # 实例化数据库配置模型
        return DataBaseSettings()

    @lru_cache()
    def get_redis_config(self):
        """
        获取Redis配置
        """
        # 实例化Redis配置模型
        return RedisSettings()

    @lru_cache()
    def get_upload_config(self):
        """
        获取数据库配置
        """
        # 实例上传配置
        return UploadSettings()

    @lru_cache()
    def get_eaviz_config(self):
        cfg = EAVizSettings()
        cfg.AddressConfig.setup()
        return cfg

    @staticmethod
    def parse_cli_args():
        """
        解析命令行参数

        分两种情况：
            1、如果通过 uvicorn.exe 指令 uvicorn app:app 启动，命令行参数按照uvicorn文档要求配置，无法解析自定义参数
            2、如果通过 python app.py --env=dev 启动，解析自定义参数
        """
        # sys.argv保存了命令行参数，第一个参数通常是启动程序的脚本名（完整路径），其后的元素是传递给脚本的其他参数
        # ['\\envs\\eaviz_ol\\Scripts\\uvicorn', 'app:app'] ['app.py', '--env=dev']
        if 'uvicorn' in argv[0]:
            pass
        else:
            # 使用argparse定义命令行参数
            parser = ArgumentParser(description='命令行参数')
            parser.add_argument('--env', type=str, default='', help='运行环境')
            # 解析命令行参数
            args = parser.parse_args()  # Namespace(env='') Namespace(env='dev')
            # 设置环境变量，如果未设置命令行参数，默认APP_ENV为dev
            environ['APP_ENV'] = args.env if args.env else 'dev'
        # 读取运行环境
        run_env = environ.get('APP_ENV', '')
        # 运行环境未指定时默认加载.env.dev
        env_file = '.env.dev'
        # 运行环境不为空时按命令行参数加载对应.env文件
        if run_env != '':
            env_file = f'.env.{run_env}'
        # 加载配置
        load_dotenv(env_file)


# 实例化获取配置类
get_config = GetConfig()
# 应用配置
AppConfig = get_config.get_app_config()
# Jwt配置
JwtConfig = get_config.get_jwt_config()
# 数据库配置
DataBaseConfig = get_config.get_database_config()
# Redis配置
RedisConfig = get_config.get_redis_config()
# 上传配置
UploadConfig = get_config.get_upload_config()
# EAViz配置
EAVizConfig = get_config.get_eaviz_config()
