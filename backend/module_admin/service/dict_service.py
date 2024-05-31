from config.env import RedisInitKeyConfig
from fastapi import Request
import json
from module_admin.dao.dict_dao import *
from module_admin.entity.vo.common_vo import CrudResponseModel
from utils.common_util import export_list2excel, CamelCaseUtil
from typing import List


class DictTypeService:
    """
    字典类型管理模块服务层
    """
    @classmethod
    def get_dict_type_list_services(cls, query_db: Session, query_object: DictTypePageQueryModel,
                                    is_page: bool = False):
        """
        获取字典类型列表信息service
        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典类型列表信息对象
        """
        dict_type_list_result = DictTypeDao.get_dict_type_list(query_db, query_object, is_page)

        return dict_type_list_result

    @classmethod
    async def add_dict_type_services(cls, request: Request, query_db: Session, page_object: DictTypeModel):
        """
        新增字典类型信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增岗位对象
        :return: 新增字典类型校验结果
        """
        dict_type = DictTypeDao.get_dict_type_detail_by_info(query_db, DictTypeModel(dictType=page_object.dict_type))
        if dict_type:
            result = dict(is_success=False, message='字典类型已存在')
        else:
            try:
                DictTypeDao.add_dict_type_dao(query_db, page_object)
                query_db.commit()
                await DictDataService.init_cache_sys_dict_services(query_db, request.app.state.redis)  # 添加后重新存一遍
                result = dict(is_success=True, message='新增成功')
            except Exception as e:
                query_db.rollback()
                raise e

        return CrudResponseModel(**result)

    @classmethod
    async def edit_dict_type_services(cls, request: Request, query_db: Session, page_object: DictTypeModel):
        """
        编辑字典类型信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 编辑字典类型对象
        :return: 编辑字典类型校验结果
        """
        edit_dict_type = page_object.model_dump(exclude_unset=True)
        dict_type_info = cls.dict_type_detail_services(query_db, edit_dict_type.get('dict_id'))
        if dict_type_info:
            if dict_type_info.dict_type != page_object.dict_type or dict_type_info.dict_name != page_object.dict_name:
                dict_type = DictTypeDao.get_dict_type_detail_by_info(query_db,
                                                                     DictTypeModel(dictType=page_object.dict_type))
                if dict_type:
                    result = dict(is_success=False, message='字典类型已存在')
                    return CrudResponseModel(**result)
            try:
                if dict_type_info.dict_type != page_object.dict_type:  # 如果字典类型发生了更改
                    query_dict_data = DictDataPageQueryModel(dictType=dict_type_info.dict_type)
                    dict_data_list = DictDataDao.get_dict_data_list(query_db, query_dict_data)  # 查询所有相关的字典数据
                    for dict_data in dict_data_list:
                        edit_dict_data = DictDataModel(dictCode=dict_data.dict_code, dictType=page_object.dict_type,
                                                       updateBy=page_object.update_by).model_dump(exclude_unset=True)
                        DictDataDao.edit_dict_data_dao(query_db, edit_dict_data)  # 更新各数据的字典类型
                DictTypeDao.edit_dict_type_dao(query_db, edit_dict_type)  # 更新数据库中的字典类型信息（dict_type为两张表共有）
                query_db.commit()
                await DictDataService.init_cache_sys_dict_services(query_db, request.app.state.redis)
                result = dict(is_success=True, message='更新成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='字典类型不存在')

        return CrudResponseModel(**result)

    @classmethod
    async def delete_dict_type_services(cls, request: Request, query_db: Session, page_object: DeleteDictTypeModel):
        """
        删除字典类型信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 删除字典类型对象
        :return: 删除字典类型校验结果
        """
        if page_object.dict_ids:
            dict_id_list = page_object.dict_ids.split(',')
            try:
                for dict_id in dict_id_list:
                    DictTypeDao.delete_dict_type_dao(query_db, DictTypeModel(dictId=dict_id))
                query_db.commit()
                await DictDataService.init_cache_sys_dict_services(query_db, request.app.state.redis)
                result = dict(is_success=True, message='删除成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='传入字典类型id为空')
        return CrudResponseModel(**result)

    @classmethod
    def dict_type_detail_services(cls, query_db: Session, dict_id: int):
        """
        获取字典类型详细信息service
        :param query_db: orm对象
        :param dict_id: 字典类型id
        :return: 字典类型id对应的信息
        """
        dict_type = DictTypeDao.get_dict_type_detail_by_id(query_db, dict_id=dict_id)
        result = DictTypeModel(**CamelCaseUtil.transform_result(dict_type))

        return result

    @staticmethod
    def export_dict_type_list_services(dict_type_list: List):
        """
        导出字典类型信息service
        :param dict_type_list: 字典信息列表
        :return: 字典信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            "dictId": "字典编号",
            "dictName": "字典名称",
            "dictType": "字典类型",
            "status": "状态",
            "createBy": "创建者",
            "createTime": "创建时间",
            "updateBy": "更新者",
            "updateTime": "更新时间",
            "remark": "备注",
        }

        data = dict_type_list

        for item in data:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
        new_data = [{mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} for item in
                    data]
        binary_data = export_list2excel(new_data)

        return binary_data

    @classmethod
    async def refresh_sys_dict_services(cls, request: Request, query_db: Session):
        """
        刷新字典缓存信息service
        :param request: Request对象
        :param query_db: orm对象
        :return: 刷新字典缓存校验结果
        """
        await DictDataService.init_cache_sys_dict_services(query_db, request.app.state.redis)
        result = dict(is_success=True, message='刷新成功')

        return CrudResponseModel(**result)


class DictDataService:
    """
    字典数据管理模块服务层
    """
    @classmethod
    def get_dict_data_list_services(cls, query_db: Session, query_object: DictDataPageQueryModel,
                                    is_page: bool = False):
        """
        获取字典数据列表信息service
        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 字典数据列表信息对象
        """
        dict_data_list_result = DictDataDao.get_dict_data_list(query_db, query_object, is_page)

        return dict_data_list_result

    @classmethod
    def query_dict_data_list_services(cls, query_db: Session, dict_type: str):
        """
        获取字典数据列表信息service
        :param query_db: orm对象
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        dict_data_list_result = DictDataDao.query_dict_data_list(query_db, dict_type)

        return dict_data_list_result

    @classmethod
    async def init_cache_sys_dict_services(cls, query_db: Session, redis):
        """
        应用初始化：获取所有字典类型对应的字典数据信息并缓存service

        1.先清除redis中所有以sys_dict:开头的键（如果存在）

        2.从数据库中获取所有字典类型信息

        3.查询字典类型的所有字典数据

        4.转换字典数据并存储到redis中

        :param query_db: orm对象
        :param redis: redis对象
        """
        # 获取以sys_dict:开头的键列表
        keys = await redis.keys(f"{RedisInitKeyConfig.SYS_DICT.get('key')}:*")  # sys_dict:*
        # 删除匹配的键
        if keys:
            await redis.delete(*keys)  # * 是一个解包运算符（unpacking operator），用于将一个列表或元组中的元素解包为多个单独的参数传递给函数，以便一次性删除多个 Redis 键
        dict_type_all = DictTypeDao.get_all_dict_type(query_db)
        for dict_type_obj in [item for item in dict_type_all if item.status == '0']:
            dict_type = dict_type_obj.dict_type
            # 查询该字典类型的所有字典数据
            dict_data_list = DictDataDao.query_dict_data_list(query_db, dict_type)
            # 转换字典数据并存储到 Redis 中
            # redis.set 方法用于在 Redis 中设置一个键值对 await redis.set(key, value)
            dict_data = [CamelCaseUtil.transform_result(row) for row in dict_data_list if row]
            await redis.set(f"{RedisInitKeyConfig.SYS_DICT.get('key')}:{dict_type}",
                            json.dumps(dict_data, ensure_ascii=False, default=str))

    @classmethod
    async def query_dict_data_list_from_cache_services(cls, redis, dict_type: str):
        """
        从缓存获取字典数据列表信息service
        :param redis: redis对象
        :param dict_type: 字典类型
        :return: 字典数据列表信息对象
        """
        result = []
        # redis.get(key) 方法用来获取 Redis 中存储的值，key 是对应的键 | 此处 key 为 sys_dict:dict_type
        dict_data_list_result = await redis.get(f"{RedisInitKeyConfig.SYS_DICT.get('key')}:{dict_type}")
        if dict_data_list_result:
            result = json.loads(dict_data_list_result)  # 反序列化为 Python 对象
            # 结果的类型取决于 JSON 字符串的内容。具体来说：
            # 如果 JSON 字符串表示一个对象（即以 {} 包围的键值对），那么 json.loads 返回一个 Python 字典（dict）。
            # 如果 JSON 字符串表示一个数组（即以 [] 包围的值列表），那么 json.loads 返回一个 Python 列表（list）。
            # 如果 JSON 字符串表示一个字符串（即以双引号包围的文本），那么 json.loads 返回一个 Python 字符串（str）。
            # 如果 JSON 字符串表示一个数字（整数或浮点数），那么 json.loads 返回相应的 Python 数字类型（int 或 float）。
            # 如果 JSON 字符串表示一个布尔值（true 或 false），那么 json.loads 返回相应的 Python 布尔值（True 或 False）。
            # 如果 JSON 字符串表示 null，那么 json.loads 返回 Python 的 None。

            # [{"dictCode": 31, "dictSort": 1, "dictLabel": "成功", "dictValue": "0", "dictType": "sys_common_status",
            # "cssClass": "", "listClass": "primary", "isDefault": "N", "status": "0", "createBy": "admin",
            # "createTime": "2024-05-05 17:10:15", "updateBy": "", "updateTime": null, "remark": "正常状态"},
            # {"dictCode": 32, "dictSort": 2, "dictLabel": "失败", "dictValue": "1", "dictType": "sys_common_status",
            # "cssClass": "", "listClass": "danger", "isDefault": "N", "status": "0", "createBy": "admin",
            # "createTime": "2024-05-05 17:10:15", "updateBy": "", "updateTime": null, "remark": "停用状态"}]
            # 转化为list

            # json.dumps 将 Python 对象转换为 JSON 格式的字符串。它的作用与 json.loads 相反：
            # json.loads 是将 JSON 字符串解析为 Python 对象，而 json.dumps 则是将 Python 对象序列化为 JSON 字符串。

        return CamelCaseUtil.transform_result(result)

    @classmethod
    async def add_dict_data_services(cls, request: Request, query_db: Session, page_object: DictDataModel):
        """
        新增字典数据信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 新增岗位对象
        :return: 新增字典数据校验结果
        """
        dict_data = DictDataDao.get_dict_data_detail_by_info(query_db, page_object)
        if dict_data:
            result = dict(is_success=False, message='字典数据已存在')
        else:
            try:
                DictDataDao.add_dict_data_dao(query_db, page_object)
                query_db.commit()
                await cls.init_cache_sys_dict_services(query_db, request.app.state.redis)
                result = dict(is_success=True, message='新增成功')
            except Exception as e:
                query_db.rollback()
                raise e

        return CrudResponseModel(**result)

    @classmethod
    async def edit_dict_data_services(cls, request: Request, query_db: Session, page_object: DictDataModel):
        """
        编辑字典数据信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 编辑字典数据对象
        :return: 编辑字典数据校验结果
        """
        existing_dict_data = cls.dict_data_detail_services(query_db, page_object.dict_code)
        if not existing_dict_data:
            return CrudResponseModel(is_success=False, message='字典数据不存在')

        conflicting_dict_data = DictDataDao.get_dict_data_detail_by_info(query_db, page_object)
        if conflicting_dict_data and conflicting_dict_data.dict_code != page_object.dict_code:
            return CrudResponseModel(is_success=False, message='存在冲突的字典数据')  # 一旦检测到冲突，应当立即停止进一步操作，并向用户反馈错误信息。

        try:
            edit_data_type = page_object.model_dump(exclude_unset=True)  # 提取页面对象中设置的数据
            DictDataDao.edit_dict_data_dao(query_db, edit_data_type)
            query_db.commit()
            await cls.init_cache_sys_dict_services(query_db, request.app.state.redis)
            return CrudResponseModel(is_success=True, message='更新成功')
        except Exception as e:
            query_db.rollback()
            return CrudResponseModel(is_success=False, message=f'更新失败: {str(e)}')

    @classmethod
    async def delete_dict_data_services(cls, request: Request, query_db: Session, page_object: DeleteDictDataModel):
        """
        删除字典数据信息service
        :param request: Request对象
        :param query_db: orm对象
        :param page_object: 删除字典数据对象
        :return: 删除字典数据校验结果
        """
        if page_object.dict_codes:
            dict_code_list = page_object.dict_codes.split(',')
            try:
                for dict_code in dict_code_list:
                    DictDataDao.delete_dict_data_dao(query_db, DictDataModel(dictCode=dict_code))
                query_db.commit()
                await cls.init_cache_sys_dict_services(query_db, request.app.state.redis)
                result = dict(is_success=True, message='删除成功')
            except Exception as e:
                query_db.rollback()
                raise e
        else:
            result = dict(is_success=False, message='传入字典数据id为空')
        return CrudResponseModel(**result)

    @classmethod
    def dict_data_detail_services(cls, query_db: Session, dict_code: int):
        """
        获取字典数据详细信息service
        :param query_db: orm对象
        :param dict_code: 字典数据id
        :return: 字典数据id对应的信息
        """
        dict_data = DictDataDao.get_dict_data_detail_by_id(query_db, dict_code=dict_code)
        result = DictDataModel(**CamelCaseUtil.transform_result(dict_data))

        return result

    @staticmethod
    def export_dict_data_list_services(dict_data_list: List):
        """
        导出字典数据信息service
        :param dict_data_list: 字典数据信息列表
        :return: 字典数据信息对应excel的二进制数据
        """
        # 创建一个映射字典，将英文键映射到中文键
        mapping_dict = {
            "dictCode": "字典编码",
            "dictSort": "字典标签",
            "dictLabel": "字典键值",
            "dictValue": "字典排序",
            "dictType": "字典类型",
            "cssClass": "样式属性",
            "listClass": "表格回显样式",
            "isDefault": "是否默认",
            "status": "状态",
            "createBy": "创建者",
            "createTime": "创建时间",
            "updateBy": "更新者",
            "updateTime": "更新时间",
            "remark": "备注",
        }

        data = dict_data_list

        for item in data:
            if item.get('status') == '0':
                item['status'] = '正常'
            else:
                item['status'] = '停用'
            if item.get('isDefault') == 'Y':
                item['isDefault'] = '是'
            else:
                item['isDefault'] = '否'
        new_data = [{mapping_dict.get(key): value for key, value in item.items() if mapping_dict.get(key)} for item in
                    data]
        binary_data = export_list2excel(new_data)

        return binary_data
