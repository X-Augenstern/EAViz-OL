from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from os import path, getcwd
from random import randint, choice
from base64 import b64encode


class CaptchaService:
    """
    验证码模块服务层
    """
    @classmethod
    def create_captcha_image_service(cls):
        """
        生成一个包含简单数学运算的验证码图像，并返回该图像的 base64 编码字符串和计算结果
        """
        # 创建空白图像
        image = Image.new('RGB', (160, 60), color='#EAEAEA')  # 背景颜色为浅灰色

        # 创建绘图对象
        draw = ImageDraw.Draw(image)

        # 设置字体
        font = ImageFont.truetype(path.join(path.abspath(getcwd()), 'assets', 'font', 'Arial.ttf'), size=30)

        # 生成两个0-9之间的随机整数
        num1 = randint(0, 9)
        num2 = randint(0, 9)
        # 从运算符列表中随机选择一个
        operational_character_list = ['+', '-', '*']
        operational_character = choice(operational_character_list)
        # 根据选择的运算符进行计算
        if operational_character == '+':
            result = num1 + num2
        elif operational_character == '-':
            result = num1 - num2
        else:
            result = num1 * num2
        # 绘制文本
        text = f"{num1} {operational_character} {num2} = ?"
        draw.text((25, 15), text, fill='blue', font=font)

        # 将图像数据保存到内存中
        buffer = BytesIO()
        image.save(buffer, format='PNG')

        # 将图像数据转换为base64字符串
        base64_string = b64encode(buffer.getvalue()).decode()

        return [base64_string, result]
