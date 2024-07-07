from fastapi import Request, BackgroundTasks
from os import path, makedirs
from fastapi import UploadFile
from datetime import datetime
from config.env import UploadConfig
from module_admin.entity.vo.common_vo import *
from utils.upload_util import UploadUtil
from typing import List


class CommonService:
    """
    通用模块服务层
    """

    @classmethod
    def upload_service(cls, request: Request, files: List[UploadFile]):
        """
        将用户上传的文件保存到服务器的指定位置，并返回上传结果service
        :param request: Request对象
        :param files: 上传文件对象
        :return: 上传结果
        """
        results = []

        for file in files:
            if not UploadUtil.check_file_extension(file):
                result = CrudResponseModel(is_success=False, message=f'{file.filename} 的类型不合法')
            else:
                # upload/2024/07/05
                relative_path = (f'upload/'
                                 f'{datetime.now().strftime("%Y")}/'
                                 f'{datetime.now().strftime("%m")}/'
                                 f'{datetime.now().strftime("%d")}')
                # files/upload_path/upload/2024/07/05
                dir_path = path.join(UploadConfig.UPLOAD_PATH, relative_path)
                try:
                    makedirs(dir_path)
                except FileExistsError:
                    pass
                # demo_edf_20240705132949A605.edf
                filename = (f'{file.filename.rsplit(".", 1)[0]}_'
                            f'{datetime.now().strftime("%Y%m%d%H%M%S")}'
                            f'{UploadConfig.UPLOAD_MACHINE}'
                            f'{UploadUtil.generate_random_number()}.'
                            f'{file.filename.rsplit(".")[-1]}')
                # files/upload_path/upload/2024/07/05/demo_edf_20240705132949A605.edf
                filepath = path.join(dir_path, filename)

                # 以二进制写模式将文件数据从一个源文件逐块写入到目标文件（流式写出大型文件）
                with open(filepath, 'wb') as f:
                    for chunk in iter(lambda: file.file.read(1024 * 1024 * 10), b''):  # 每次调用它都会从 file.file 读取 10 MB 的数据
                        # iter 函数创建一个迭代器，每次调用迭代器时，它都会调用 lambda 函数以获取下一个值（在这里是读取的文件数据块）
                        # b'' 是哨兵值，当 file.file.read 返回空字节串（即文件已读取完毕）时，迭代结束
                        # eg：file.file 是一个大小为 25 MB 的文件，代码执行过程如下：
                        # 第一次调用 lambda 函数，读取第一个 10 MB 数据块。
                        # 第二次调用 lambda 函数，读取第二个 10 MB 数据块。
                        # 第三次调用 lambda 函数，读取剩余的 5 MB 数据块。
                        # 第四次调用 lambda 函数，返回 b''（因为文件已读取完毕）。
                        # 迭代器检测到返回值等于哨兵值 b''，迭代停止。

                        f.write(chunk)

                result = CrudResponseModel(
                    is_success=True,
                    result=UploadResponseModel(
                        # 在 model 中定义了 alias_generator 后创建模型实例使用的属性要按别名转化后来使用，否则模型内的值就为 None
                        # e.g. : model_config = ConfigDict(alias_generator=to_pascal)
                        # voice = Voice(Name='Filiz', LanguageCode='tr-TR')
                        # print(voice.language_code)
                        # #> tr-TR
                        # print(voice.model_dump(by_alias=True))
                        # #> {'Name': 'Filiz', 'LanguageCode': 'tr-TR'}
                        # /profile/upload/2024/07/05/demo_edf_20240705132949A605.edf
                        fileName=f'{UploadConfig.UPLOAD_PREFIX}/{relative_path}/{filename}',
                        # demo_edf_20240705132949A605.edf
                        newFileName=filename,
                        # demo_edf.edf
                        originalFilename=file.filename,
                        # http://localhost:9099/profile/upload/2024/07/05/demo_edf_20240705132949A605.edf
                        # url=f'{str(request.base_url).replace("/dev-api","")}'
                        #     f'{UploadConfig.UPLOAD_PREFIX[1:]}/{relative_path}/{filename}',
                        filePath=filepath
                    ),
                    message=f'{file.filename} 上传成功'
                )
                # test
                # logger.error(result.result.file_name)
                # logger.error(result.result.model_dump(by_alias=True))
            results.append(result)

        return results

    @classmethod
    def download_services(cls, background_tasks: BackgroundTasks, file_name, delete: bool):
        """
        下载下载目录文件service
        :param background_tasks: 后台任务对象
        :param file_name: 下载的文件名称
        :param delete: 是否在下载完成后删除文件
        :return: 含有根据文件生成二进制数据的操作响应
        """
        filepath = path.join(UploadConfig.DOWNLOAD_PATH, file_name)  # 服务器上存储待下载文件的完整路径 eaviz/download_path/file_name
        if '..' in file_name:
            result = dict(is_success=False, message='文件名称不合法')  # 避免目录遍历攻击
        elif not UploadUtil.check_file_exists(filepath):
            result = dict(is_success=False, message='文件不存在')
        else:
            result = dict(is_success=True, result=UploadUtil.generate_file(filepath), message='下载成功')
            if delete:
                background_tasks.add_task(UploadUtil.delete_file, filepath)  # 异步删除文件
        return CrudResponseModel(**result)

    @classmethod
    def download_resource_services(cls, resource: str):
        """
        下载上传目录文件service
        :param resource: 下载的文件名称
        :return: 含有根据文件生成二进制数据的操作响应
        """
        # <request.base_url>eaviz/upload_path/upload/2024/05/26/filename_20240526A999.extension
        filepath = path.join(resource.replace(UploadConfig.UPLOAD_PREFIX, UploadConfig.UPLOAD_PATH))
        filename = resource.rsplit("/", 1)[-1]
        if '..' in filename or not UploadUtil.check_file_timestamp(filename) or not UploadUtil.check_file_machine(
                filename) or not UploadUtil.check_file_random_code(filename):
            result = dict(is_success=False, message='文件名称不合法')
        elif not UploadUtil.check_file_exists(filepath):
            result = dict(is_success=False, message='文件不存在')
        else:
            result = dict(is_success=True, result=UploadUtil.generate_file(filepath), message='下载成功')
        return CrudResponseModel(**result)
