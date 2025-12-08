from datetime import datetime
from fastapi import UploadFile
from os import remove, path
from random import randint

from config.env import UploadConfig


class UploadUtil:
    """
    上传工具类
    """

    @classmethod
    def generate_random_number(cls):
        """
        生成3位数字构成的字符串
        """
        random_number = randint(1, 999)

        return f'{random_number:03}'  # :03 是格式说明符：0 表示用零填充 | 3 表示总长度为 3

    @classmethod
    def check_file_exists(cls, filepath):
        """
        检查文件是否存在
        """
        return path.exists(filepath)

    @classmethod
    def check_file_extension(cls, file: UploadFile):
        """
        检查文件后缀是否合法
        """
        file_extension = file.filename.rsplit('.', 1)[-1]
        if file_extension in UploadConfig.DEFAULT_ALLOWED_EXTENSION:
            return True
        return False

    @classmethod
    def check_file_timestamp(cls, filename):
        """
        校验文件时间戳是否合法
        """
        # rsplit('.', 1) 从右边开始，按点号（.）分割 filename，最多分割一次。这将文件名分割成两部分：主文件名和扩展名

        # filename_20240526A999.extension -> 20240526
        timestamp = filename.rsplit('.', 1)[0].split('_')[-1].split(UploadConfig.UPLOAD_MACHINE)[0]
        try:
            datetime.strptime(timestamp, '%Y%m%d%H%M%S')  # 将字符串解析为 datetime 对象
            return True
        except ValueError:
            return False

    @classmethod
    def check_file_machine(cls, filename):
        """
        校验文件机器码是否合法
        """
        if filename.rsplit('.', 1)[0][-4] == UploadConfig.UPLOAD_MACHINE:
            return True
        return False

    @classmethod
    def check_file_random_code(cls, filename):
        """
        校验文件随机码是否合法
        """
        valid_code_list = [f"{i:03}" for i in range(1, 999)]
        if filename.rsplit('.', 1)[0][-3:] in valid_code_list:  # filename_20240526A999.extension -> 999
            return True
        return False

    @classmethod
    def generate_file(cls, filepath):
        """
        根据文件生成二进制数据

        将文件 filepath 的内容作为生成器返回，每次迭代时，生成文件的一部分数据。这样可以在处理大文件时节省内存，因为文件内容是逐步读取的，而不是一次性读取到内存中。

        yield from response_file 会把整个文件内容一次性读入内存。这对于大文件来说并不理想。为了逐步读取文件的内容，我们需要在读取过程中控制读取的块大小。

        以下是修正后的 generate_file 方法，它将逐步读取文件内容并生成二进制数据块：
        e. g. :
        chunk_size = 8192 # 默认块大小为 8192 字节（8KB）
        with open(filepath, 'rb') as response_file:  # 二进制读模式（'rb'）打开
            while True:
                data = response_file.read(chunk_size)
                if not data:
                    break
                yield data

        Note:
            yield from 是 Python 3.3 引入的一个语法，用于在生成器中委派到另一个生成器。它会迭代 response_file，并逐行返回每一行的内容。这样，每次调用生成器时，它会从文件中读取一行并返回。
            这对于逐行读取文件内容非常有用，特别是在处理大文件时，可以节省内存。

            yield response_file 只是简单地返回 response_file 对象本身，并不会迭代它的内容。如果你这样做，调用生成器时只会得到文件对象，而不是文件内容。
            这通常不是想要的行为，尤其是当你希望逐步读取和处理文件内容时。

            e. g. : 假设有一个文件 example.txt，内容如下：
            Hello,
            World!

            use yield from:
            def generate_file(filepath):
                with open(filepath, 'rb') as response_file:
                    yield from response_file

            for line in generate_file('example.txt'):
                print(line)

            ->  b'Hello,\n'
                b'World!\n'

            use yield:
            def generate_file(filepath):
                with open(filepath, 'rb') as response_file:
                    yield response_file

            for file in generate_file('example.txt'):
                print(file)

            -> <_io.BufferedReader name='example.txt'> 输出将是文件对象本身，而不是文件内容

            ∴ yield from 适用于读取文件内容
              yield 适用于二进制数据
        """
        # eg: Hello,
        #     World!
        #
        # for line in generate_file(filepath):
        #     print(line)
        #
        # -> b'Hello,\n'
        #    b'World!\n'
        with open(filepath, 'rb') as response_file:  # 二进制读模式（'rb'）打开
            yield from response_file  # 允许从一个可迭代对象中生成值，将文件内容逐行生成，每次迭代都会生成文件中的下一行数据，直到文件结束

    @classmethod
    def delete_file(cls, filepath: str):
        """
        根据文件路径删除对应文件
        """
        remove(filepath)
