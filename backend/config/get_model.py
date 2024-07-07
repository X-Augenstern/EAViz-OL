from config.env import EAVizConfig
from asyncio import to_thread
from utils.log_util import logger
from exceptions.exception import ModelLoadingException
from os import path
from torch import load
from eaviz.ESC_SD.ESC.A3D_model import R3DClassifier
from eaviz.ESC_SD.SD.two_feature_model import Classifier1D_2D_3D


class ModelUtil:

    @classmethod
    def _get_cp_address(cls, item_name):
        # 若获取不到： F:\Python\EAViz_OL\backend\
        return path.abspath(EAVizConfig.cp_address.get(item_name, ''))

    @classmethod
    async def _init_esc_sd(cls, item_name=None):
        def _create_r3d_classifier():
            return R3DClassifier(8, (2, 2, 2, 2), pretrained=True)

        def _create_classifier1d_2d_3d():
            return Classifier1D_2D_3D(2, (2, 2, 2, 2), pretrained=True)

        async def _load_model(model_creator, i_name):
            try:
                # 只要一个函数中使用了 await，这个函数本身就必须使用 async 声明。
                # 进一步，如果一个函数调用了这个 async 函数，那么这个调用者函数也必须是 async，以便它能够 await 被调用的异步函数。
                model = model_creator()
                # 将加载操作放在一个线程中执行，避免阻塞事件循环
                logger.info(cls._get_cp_address(i_name))
                checkpoint = await to_thread(load, cls._get_cp_address(i_name),
                                             map_location=lambda storage, loc: storage)
                model.load_state_dict(checkpoint['state_dict'])
                model.eval()
                return model
            except ModelLoadingException as e:
                logger.error(f"{i_name} 的预训练模型初始化失败: {e}")
                return None

        esc_model, sd_model = None, None

        if item_name == 'ESC':
            esc_model = await _load_model(_create_r3d_classifier, item_name)
        elif item_name == 'SD':
            sd_model = await _load_model(_create_classifier1d_2d_3d, item_name)
        else:
            esc_model = await _load_model(_create_r3d_classifier, 'ESC')
            sd_model = await _load_model(_create_classifier1d_2d_3d, 'SD')
        return [esc_model, sd_model]

    @classmethod
    async def init_models(cls, item_name=None):
        """
        :param item_name: None初始化全部预训练模型，否则只初始化对应的模型
        """
        model_dict = {}
        if item_name is None:
            logger.info("开始初始化所有预训练模型...")
        else:
            logger.info(f"开始初始化 {item_name} 的预训练模型...")
        if item_name in ['ESC', 'SD']:
            models = await cls._init_esc_sd(item_name)
            if models[0] is None:
                model_dict[item_name] = models[1]
            elif models[1] is None:
                model_dict[item_name] = models[0]
            logger.info(f"{item_name} 的预训练模型初始化成功")
        else:
            models = await cls._init_esc_sd()
            for item, model in zip(EAVizConfig.item_name, models):
                if model is not None:
                    model_dict[item] = model
            if len(model_dict.keys()) == len(EAVizConfig.item_name):
                logger.info("所有预训练模型初始化成功")
            else:
                logger.error("存在预训练模型初始化失败")
        return model_dict
