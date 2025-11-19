from config.env import EAVizConfig
from asyncio import to_thread
from utils.log_util import logger
from exceptions.exception import ModelLoadingException
from torch import load
from eaviz.ESC_SD.ESC.A3D_model import R3DClassifier
from eaviz.ESC_SD.SD.two_feature_model import Classifier1D_2D_3D
from eaviz.AD.model.Loss import classLoss  # 引入损失的类函数
from eaviz.AD.model.R2D import resnet34
from eaviz.AD.model.densenet import DenseNet121
from eaviz.AD.model.googlenet import GoogLeNet
from eaviz.AD.model.senet import SENet18
from eaviz.AD.model.vgg import VGG16
from eaviz.AD.AE_Combine import AutoEncoder, SkipAutoEncoder, MemAutoEncoder, EstimatorAutoEncoder, Resnet_Encoder, VAE


class ModelUtil:
    @classmethod
    async def _init_esc_sd(cls, model_dict):
        def _create_r3d_classifier():
            return R3DClassifier(8, (2, 2, 2, 2), pretrained=True)

        def _create_classifier1d_2d_3d():
            return Classifier1D_2D_3D(2, (2, 2, 2, 2), pretrained=True)

        async def _load_model(model_creator, cp_adr):
            try:
                # 只要一个函数中使用了 await，这个函数本身就必须使用 async 声明。
                # 进一步，如果一个函数调用了这个 async 函数，那么这个调用者函数也必须是 async，以便它能够 await 被调用的异步函数。
                model = model_creator()
                # 将加载操作放在一个线程中执行，避免阻塞事件循环
                checkpoint = await to_thread(load, cp_adr, map_location=lambda storage, loc: storage)
                model.load_state_dict(checkpoint['state_dict'])
                model.eval()
                return model
            except ModelLoadingException as e:
                logger.error(f"{cp_adr} 预训练模型初始化失败: {e}")
                return None

        try:
            model = None
            logger.info(EAVizConfig.AddressConfig.get_cp_adr('ESC_SD'))
            address_dict = EAVizConfig.AddressConfig.get_cp_adr('ESC_SD')
            for k, v in address_dict.items():
                if k == 'R3DClassifier':
                    model = await _load_model(_create_r3d_classifier, v)
                elif k == 'DSMN-ESS':
                    model = await _load_model(_create_classifier1d_2d_3d, v)
                if model is not None:
                    model_dict[k] = model
        except ModelLoadingException as e:
            logger.error(f"ESC_SD 的预训练模型初始化失败: {e}")
            return None

    @classmethod
    async def _init_ad(cls, model_dict):
        def _prepare_model1(model, test_weight, test=False):
            printout = 'Using Model: ' + model
            if model == 'Resnet34':
                model = resnet34(loss=classLoss())  # 修改损失
                print('**************************************** Using ResNet34 ***************************************')
            elif model == 'SENet18':
                model = SENet18(loss=classLoss())  # 修改损失
                print('**************************************** Using SENet18 ****************************************')
            elif model == 'DenseNet121':
                model = DenseNet121(loss=classLoss())
                print('**************************************** Using DenseNet121 ************************************')
            elif model == "VGG16":
                model = VGG16(loss=classLoss())
                print('***************************************** Using VGG16 *****************************************')
            elif model == "GoogLeNet":
                model = GoogLeNet(loss=classLoss())
            else:
                raise NotImplementedError
            if test:
                state_dict = load(test_weight)['state_dict']
                model.load_state_dict(state_dict)
                print(' Weight_path: ' + test_weight)
            print(printout)
            return model.float().cuda().eval()

        def _prepare_model2(model, test_weight=None):  # AE 的模型
            assert model in ['AE', 'SkipAE', 'MemAE', 'EstimatorAutoEncoder', 'VAE', 'Resnet_Encoder']
            if model == 'AE':
                model = AutoEncoder(with_last_relu=False)
                print('***************************************** Using AE *****************************************')
            elif model == 'SkipAE':
                model = SkipAutoEncoder(with_last_relu=False)
                print('**************************************** Using SkipAE *****************************************')
            elif model == 'MemAE':
                model = MemAutoEncoder(with_last_relu=False)
                print('***************************************** Using MemAE *****************************************')
            elif model == 'EstimatorAutoEncoder':
                model = EstimatorAutoEncoder(with_last_relu=False)
            elif model == 'Resnet_Encoder':
                model = Resnet_Encoder(with_last_relu=False)
            elif model == 'VAE':
                model = VAE(1000)
                print('***************************************** Using VAE *****************************************')
            else:
                raise NotImplementedError
            if test_weight:
                state_dict = load(test_weight)['state_dict']
                model.load_state_dict(state_dict)
                print(f'loading model {model} with weight {test_weight}')
            else:
                print(f'loading model {model}')
            return model.float().cuda().eval()

        try:
            model = None
            logger.info(EAVizConfig.AddressConfig.get_cp_adr('AD'))
            address_dict = EAVizConfig.AddressConfig.get_cp_adr('AD')
            for k, v in address_dict.items():
                if k in ['Resnet34', 'VGG16', 'SENet18', 'DenseNet121']:
                    model = _prepare_model1(k, v, test=True)
                elif k in ['AE', 'SkipAE', 'MemAE', 'VAE']:
                    model = _prepare_model2(k, v)
                if model is not None:
                    model_dict[k] = model
        except ModelLoadingException as e:
            logger.error(f"AD 的预训练模型初始化失败: {e}")
            return None

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
        await cls._init_esc_sd(model_dict)
        await cls._init_ad(model_dict)
        if len(model_dict.keys()) == EAVizConfig.ModelConfig.MODEL_NUM:
            logger.info("所有预训练模型初始化成功")
        else:
            logger.error("存在预训练模型初始化失败或未配置初始化")
        return model_dict
