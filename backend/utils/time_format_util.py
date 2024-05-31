from datetime import datetime


def object_format_datetime(obj):
    """
    :param obj: 输入一个对象
    :return:对目标对象所有datetime类型的属性格式化
    """
    # dir()用于尝试列出一个对象的所有属性和方法。这是一个非常有用的内置函数，尤其是想要快速了解一个对象提供了哪些功能时
    # 对一个对象使用 dir() 函数时，它会返回一个包含该对象的所有属性和方法名称的列表。
    # 这个列表中包括所有可访问的公有和私有属性、方法，以及从其父类继承的属性和方法
    # 对于模块，dir() 列出所有类型的名称，包括函数、类、变量等。
    # 对于类，它列出了所有的方法（包括继承的方法）和内部类。
    # 对于字符串、列表、字典等内置数据类型，它会列出这些数据类型特有的方法和属性。

    # 获取attr名称对应的属性值。getattr(obj, attr)是一个内置函数，用来从obj中获取名为attr的属性的值
    for attr in dir(obj):
        value = getattr(obj, attr)
        if isinstance(value, datetime):
            setattr(obj, attr, value.strftime('%Y-%m-%d %H:%M:%S'))
    return obj


def list_format_datetime(lst):
    """
    :param lst: 输入一个嵌套对象的列表
    :return: 对目标列表中所有对象的datetime类型的属性格式化
    """
    for obj in lst:
        for attr in dir(obj):
            value = getattr(obj, attr)
            if isinstance(value, datetime):
                setattr(obj, attr, value.strftime('%Y-%m-%d %H:%M:%S'))
    return lst


def format_datetime_dict_list(dicts):
    """
    递归遍历嵌套字典，并将 datetime 值转换为字符串格式
    :param dicts: 输入一个嵌套字典的列表
    :return: 对目标列表中所有字典的datetime类型的属性格式化
    """
    result = []

    for item in dicts:
        new_item = {}
        for k, v in item.items():
            if isinstance(v, dict):
                # 递归遍历子字典
                new_item[k] = format_datetime_dict_list([v])[0]
            elif isinstance(v, datetime):
                # 如果值是 datetime 类型，则格式化为字符串
                new_item[k] = v.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 否则保留原始值
                new_item[k] = v
        result.append(new_item)

    return result
