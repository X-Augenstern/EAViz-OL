from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.dao.edf_dao import *
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from utils.edf_util import EdfUtil
from config.env import EAVizConfig
from mne import io
from os.path import exists, abspath


class EdfService:
    """
    Edf管理模块服务层
    """

    @classmethod
    def get_edf_by_id_services(cls, query_db: Session, edf_id: int):
        """
        根据edf的id获取edf信息service
        """
        edf_res = EdfDao.get_edf_by_id(query_db, edf_id)
        return EdfModel(**CamelCaseUtil.transform_result(edf_res))

    @classmethod
    def get_edf_list_services(cls, query_db: Session, user_id: int, query_object: EdfPageQueryModel,
                              is_page: bool = False):
        """
        获取edf信息service
        """
        edf_list_result = EdfDao.get_edf_list(query_db, user_id, query_object, is_page)
        return edf_list_result

    @classmethod
    def get_edf_list_by_user_id_services(cls, query_db: Session, page_object: EdfUserPageQueryModel,
                                         is_page: bool = False):
        """
        根据用户id获取用户拥有的Edf列表信息Service
        """
        edf_user_list = EdfDao.get_edf_list_by_user_id(query_db, page_object, is_page)
        return edf_user_list

    @classmethod
    def add_edf_services(cls, query_db: Session, page_object: AddEdfModel):
        """
        新增Edf信息service
        """
        result = dict(is_success=True, message='')
        messages = []
        try:
            for edf in page_object.edf_list:
                added_edf = EdfDao.add_edf_dao(query_db, edf)
                logger.error(added_edf.edf_id)
                if not added_edf:
                    result['is_success'] = False
                    messages.append(f'{edf.edf_name} 已存在')
                else:
                    EdfDao.add_edf_user_dao(query_db, EdfUserModel(edfId=added_edf.edf_id, userId=page_object.user_id))
                    messages.append(f'{edf.edf_name} 添加成功')
            query_db.commit()
        except Exception as e:
            query_db.rollback()
            raise e

        result['message'] = ';'.join(messages)
        return CrudResponseModel(**result)

    @classmethod
    def delete_edf_services(cls, query_db: Session, page_object: DeleteEdfModel):
        """
        删除Edf信息Service
        """
        result = dict(is_success=True, message='删除成功')
        if page_object.edf_ids:
            edf_id_list = page_object.edf_ids.split(',')
            try:
                for edf_id in edf_id_list:
                    edf_id_dict = dict(edfId=edf_id)
                    EdfDao.delete_edf_dao(query_db, EdfModel(**edf_id_dict))
                    EdfDao.delete_edf_user_dao(query_db, EdfUserModel(**edf_id_dict))
                query_db.commit()
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result['is_success'] = False
            result['message'] = '传入EDF ID为空'
        return CrudResponseModel(**result)

    @classmethod
    def get_edf_data_by_id_services(cls, query_db: Session, query_object: EdfDataQueryModel):
        """
        根据edf的id以及所选通道获取edf数据service
        """
        result = dict(is_success=False, message='')
        # if not query_object.selected_channels:
        #     selected_channels = EAVizConfig.channels_21
        # else:
        #     selected_channels = query_object.selected_channels
        selected_channels = EAVizConfig.channels_21

        logger.error(f'selected_channels: {selected_channels}')

        try:
            edf_abs_path = abspath(EdfDao.get_edf_by_id(query_db, query_object.edf_id).edf_path)
            logger.error(edf_abs_path)
            if not exists(edf_abs_path):
                result['message'] = '当前文件不存在，请重新导入！'
            else:
                raw = io.read_raw_edf(edf_abs_path, preload=True)
                raw_channels = raw.info['ch_names']
                logger.error(f'raw_channels: {raw_channels}')

                selected_channels, mapping_list = EdfUtil.map_channels(selected_channels, raw_channels)
                logger.info(f'selected_list(after) = {selected_channels}')
                logger.info(f'mapping_list = {mapping_list}')
                assert len(mapping_list) == len(selected_channels), (
                    f"Error: Length mismatch between mapping_list ({len(mapping_list)}) "
                    f"and selected_channels ({len(selected_channels)})"
                )

                # 按映射表调整通道顺序，去除多余的通道
                raw.reorder_channels(mapping_list)

                # 修改通道名
                dic = {}
                for i in range(len(mapping_list)):
                    dic[mapping_list[i]] = selected_channels[i]
                raw.rename_channels(dic)
                # raw.pick(picks=selected_channels)  # 会改变raw的通道，且通道名称会按list的指定顺序排列

                result['result'] = EdfDataChunkModel(data=raw.get_data().tolist(),
                                                     sfreq=raw.info['sfreq'],
                                                     channelNames=raw.info['ch_names'])
                result['message'] = f'成功获取ID为 {query_object.edf_id} 的EDF的数据'
                result['is_success'] = True
        except Exception as e:
            logger.error(f'Invalid .edf! Error info: {str(e)}')
            result['message'] = f'Invalid .edf! Error info: {str(e)}'
            raise e

        return CrudResponseModel(**result)
