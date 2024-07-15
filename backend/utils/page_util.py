from math import ceil
from typing import Optional, List
from sqlalchemy.orm.query import Query
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from utils.common_util import CamelCaseUtil


class PageResponseModel(BaseModel):
    """
    列表分页查询返回模型
    """
    model_config = ConfigDict(alias_generator=to_camel)

    rows: List = []
    page_num: Optional[int] = None
    page_size: Optional[int] = None
    total: int
    has_next: Optional[bool] = None


class PageUtil:
    """
    分页工具类
    """

    @classmethod
    def get_page_obj(cls, data_list: List, page_num: int, page_size: int):
        """
        输入数据列表data_list和分页信息，返回分页数据列表结果
        :param data_list: 原始数据列表
        :param page_num: 当前页码
        :param page_size: 当前页面数据量
        :return: 分页数据对象
        """
        # 计算起始索引和结束索引
        start = (page_num - 1) * page_size
        end = page_num * page_size

        # 根据计算得到的起始索引和结束索引对数据列表进行切片
        paginated_data = data_list[start:end]
        has_next = True if ceil(len(data_list) / page_size) > page_num else False

        result = PageResponseModel(
            rows=paginated_data,
            pageNum=page_num,
            pageSize=page_size,
            total=len(data_list),
            hasNext=has_next
        )

        return result

    @classmethod
    def paginate(cls, query: Query, page_num: int, page_size: int, is_page: bool = False, exclude_columns=None):
        """
        输入查询语句和分页信息，返回分页数据列表结果
        :param query: sqlalchemy查询语句
        :param page_num: 当前页码
        :param page_size: 当前页面数据量
        :param is_page: 是否开启分页
        :param exclude_columns: 排除指定的列名
        :return: 分页数据对象
        """
        if is_page:
            total = query.count()
            # offset()：指定从查询结果中跳过前面多少条记录后开始获取数据。这是实现分页功能的关键一环，允许用户只查看结果集的一部分，而不是一次性加载所有数据。
            paginated_data = query.offset((page_num - 1) * page_size).limit(page_size).all()
            has_next = True if ceil(len(paginated_data) / page_size) > page_num else False
            result = PageResponseModel(
                rows=CamelCaseUtil.transform_result(PageUtil.handle_exclude_columns(paginated_data, exclude_columns)),
                pageNum=page_num,
                pageSize=page_size,
                total=total,
                hasNext=has_next
            )
        else:
            no_paginated_data = query.all()
            result = CamelCaseUtil.transform_result(PageUtil.handle_exclude_columns(no_paginated_data, exclude_columns))

        return result

    @classmethod
    def handle_exclude_columns(cls, results, exclude_columns):
        """
        从分页列表数据中排除指定的列名数据
        """
        if not results or not exclude_columns:
            return results

        processed_results = []
        for res in results:
            res_dict = {column.name: getattr(res, column.name) for column in res.__table__.columns
                        if column.name not in exclude_columns}
            processed_results.append(res_dict)

        # logger.error(f"results: {results}")  # module_admin.entity.do.edf_do.SysEdf
        # logger.error(f'res: {res}')  # module_admin.entity.do.edf_do.SysEdf

        # ReadOnlyColumnCollection(sys_edf.edf_id, sys_edf.edf_name, sys_edf.edf_sfreq, sys_edf.edf_time,
        # sys_edf.edf_path, sys_edf.valid_channels, sys_edf.upload_by, sys_edf.upload_time, sys_edf.remark)
        # logger.error(f'res.__table__.columns: {res.__table__.columns}')

        # logger.error(f'column: {column}')  # column: sys_edf.edf_id
        # logger.error(f'column.name: {column.name}')  # column.name: edf_id
        # logger.error(f'getattr(result, column.name): {getattr(result, column.name)}')  # 2

        # [{'edf_id': 2, 'edf_name': 'liang_19_sd.edf', 'edf_sfreq': 500.0, 'edf_time': 600.0,
        # 'valid_channels': 'Fp1,Fp2,F3,F4,C3,C4,P3,P4,O1,O2,F7,F8,T3,T4,T5,T6,Fz,Cz,Pz',
        # 'upload_by': 'admin', 'upload_time': datetime.datetime(2024, 7, 11, 13, 33, 45), 'remark': ''},
        # {'edf_id': 6, 'edf_name': 'demo_edf.edf', 'edf_sfreq': 200.0, 'edf_time': 45.0,
        # 'valid_channels': 'Fp1,Fp2,F3,F4,C3,C4,P3,P4,O1,O2,F7,F8,T3,T4,T5,T6,Fz,Cz,Pz',
        # 'upload_by': 'admin', 'upload_time': datetime.datetime(2024, 7, 11, 14, 12, 8), 'remark': ''}]
        # logger.error(f'processed_results: {processed_results}')
        return processed_results
