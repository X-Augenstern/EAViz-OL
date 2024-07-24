from module_admin.entity.vo.common_vo import CrudResponseModel
from module_admin.dao.edf_dao import *
from utils.common_util import CamelCaseUtil
from utils.log_util import logger
from mne import io
from os.path import exists


class EdfService:
    """
    Edf管理模块服务层
    """
    data_cache = {}

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
        try:
            edf_record = EdfDao.get_edf_by_id(query_db, query_object.edf_id)
            if not edf_record:
                result['message'] = '未找到对应的EDF记录，请重新导入！'
                return CrudResponseModel(**result)
            edf_path = edf_record.edf_path
            if not exists(edf_path):
                result['message'] = '此EDF文件不存在，请重新导入！'
                return CrudResponseModel(**result)

            raw = io.read_raw_edf(edf_path)
            if query_object.selected_channels:
                selected_channels = query_object.selected_channels.split(',')
                raw.pick(selected_channels)
            data = raw.get_data()
            start = query_object.start
            end = query_object.end  # end = None 表示到最后一个样本点（对于numpy，切片时如果不指定结束位置，即使用:，将自动扩展到数组的末尾）
            if not start:
                start = 0
            # for i in range(len(data)):  # 用于测试前端接收到的数据是按行发送的还是按列发送的
            #     logger.error(data[i][:10])
            if start < 0 or (end is not None and end > data.shape[1]) or start >= (
                    end if end is not None else data.shape[1]):
                result['message'] = 'Invalid range！'
                return CrudResponseModel(**result)
            logger.error(data[:, start:end].shape)
            result['result'] = data[:, start:end]
            result['message'] = f'成功获取ID为 {query_object.edf_id} 的EDF的数据！'
            result['is_success'] = True
            return CrudResponseModel(**result)
        except Exception as e:
            logger.error(f'Invalid .edf! Error info: {str(e)}')
            result['message'] = f'Invalid .edf! Error info: {str(e)}'
            raise e
