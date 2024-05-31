from inspect import Parameter, signature
from typing import Type
from fastapi import Query, Form
from pydantic import BaseModel
from pydantic.fields import FieldInfo

"""
Form 和 Query 是 FastAPI 中用于处理不同类型请求参数的方法。

Form
当需要向服务器提交数据以进行某种操作（如创建、更新、删除），通常使用 POST 请求，并通过 Form 从 HTTP 请求的表单数据中提取键值对。
主要在处理 application/x-www-form-urlencoded 或 multipart/form-data 类型的请求时使用，例如通过网页表单提交的数据。

Query
当需要从服务器获取数据且不涉及数据修改时，通常使用 GET 请求，并通过 Query 提取 URL 查询参数，例如 /items/?skip=0&limit=10。
Query 用于从 URL 查询参数中提取值。查询参数是附加在 URL 后面的键值对，形式为 ?key1=value1&key2=value2。

as_query:
适用于 GET 请求，因为查询参数自然在 URL 中传递。方便用户通过浏览器地址栏直接访问或书签保存。

as_form:
适用于 POST 请求，因为表单数据在请求体中传递。常用于提交表单数据，例如登录表单、搜索表单或其他需要通过表单提交的数据。

e. g. Query
@app.get("/system_user_list/")
async def get_system_user_list(request: Request,
                               user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query),
                               query_db: Session = Depends(get_db),
                               data_scope_sql: str = Depends(GetDataScope('SysUser'))):
    # 处理逻辑
    pass

使用 as_query:
user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_query)：从 URL 查询参数中提取数据，并使用 Pydantic 模型进行验证。
示例 URL: http://127.0.0.1:8000/system_user_list/?page=1&size=10&search=keyword
查询参数 page, size, search 将通过 Query 提取。

e. g. Form
@userController.post("/export", dependencies=[Depends(CheckUserInterfaceAuth('system:user:export'))])
@log_decorator(title='用户管理', business_type=5)
async def export_system_user_list(request: Request,
                                  user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_form),
                                  query_db: Session = Depends(get_db),
                                  data_scope_sql: str = Depends(GetDataScope('SysUser'))):
    # 处理逻辑
    pass

使用 as_form:
user_page_query: UserPageQueryModel = Depends(UserPageQueryModel.as_form)：从表单数据中提取数据，并使用 Pydantic 模型进行验证。
表单数据通过 POST 请求的表单提交方式传递。
<form action="/export" method="post">
  <input type="text" name="page" value="1">
  <input type="text" name="size" value="10">
  <input type="text" name="search" value="keyword">
  <input type="submit" value="Export">
</form>
"""


def as_query(cls: Type[BaseModel]):
    """
    pydantic模型查询参数装饰器，将pydantic模型用于接收查询参数


    具体来说，这段代码的主要功能是：

    1、创建新的查询参数：遍历 BaseModel 的字段，为每个字段创建一个对应的查询参数。如果字段是必需的，则查询参数必须提供值；如果字段不是必需的，则查询参数可以有一个默认值。

    2、定义新函数：定义一个新的异步函数 as_query_func，该函数接受查询参数并用这些参数实例化模型。

    3、修改函数签名：使用 inspect 模块获取新函数的签名，并用生成的查询参数替换签名中的参数列表。

    4、将新函数添加到类中：将新定义的函数作为 as_query 方法添加到类中，并返回修改后的类。

    5、最终效果是：类 cls 拥有了一个新的 as_query 方法，该方法接受查询参数并用这些参数创建类的实例。这样，原本需要手动创建实例的过程现在可以通过查询参数自动完成，简化了从查询参数到模型实例的转换过程。

    总结来说，这段代码并不是通过传统的装饰器语法直接修饰类或函数，而是通过动态修改类的方法签名，实现了类似装饰器的效果，即为类添加了一个新的方法，并改变了该方法的参数列表。
    """
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():  # 遍历模型字段
        model_field: FieldInfo  # type: ignore

        if not model_field.is_required():  # 如果字段不是必需的（即有默认值或不是强制提供的）
            # 创建一个带有默认值的 inspect.Parameter 对象，并将其添加到 new_parameters 列表中
            new_parameters.append(
                Parameter(
                    model_field.alias,  # 参数的名称
                    Parameter.POSITIONAL_ONLY,  # 参数的类型：这个参数是位置参数（不能作为关键字参数传递）
                    default=Query(model_field.default),  # 参数的默认值
                    annotation=model_field.annotation  # 参数的类型注解
                )
            )
        else:  # 如果字段是必需的（即没有默认值或必须提供）
            # 创建一个必须提供值的 inspect.Parameter 对象，并将其添加到 new_parameters 列表中
            new_parameters.append(
                Parameter(
                    model_field.alias,
                    Parameter.POSITIONAL_ONLY,
                    # 在 FastAPI 和 Pydantic 中，... 是一个特殊的标记，用于指示一个字段是必需的。
                    # 这种用法在 FastAPI 的 Query, Body, Path, 和 Header 等函数中广泛使用。
                    # 具体来说，使用 ... 作为默认值，表明该字段在请求中必须提供
                    default=Query(...),
                    annotation=model_field.annotation
                )
            )

    async def as_query_func(**data):
        """
        接收查询参数并用这些参数实例化模型
        """
        return cls(**data)

    """
    def example_func(a, b, /, c, d, *, e, f):  / 用于分隔位置参数和位置或关键字参数，* 用于分隔位置或关键字参数和仅关键字参数
        print(a, b, c, d, e, f)
    
    example_func(1, 2, 3, 4, e=5, f=6)  # 通过位置传递 a, b, c, d
    example_func(1, 2, c=3, d=4, e=5, f=6)  # 通过位置传递 a, b，通过关键字传递 c, d
    
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        print(param.kind, param.name)
        
    -> POSITIONAL_ONLY a
       POSITIONAL_ONLY b
       POSITIONAL_OR_KEYWORD c
       POSITIONAL_OR_KEYWORD d
       KEYWORD_ONLY e
       KEYWORD_ONLY f
    
    在这个函数中：
    a 和 b 是仅位置参数（Positional-Only Parameters），只能通过位置传递。
    c 和 d 是位置或关键字参数（Positional or Keyword Parameters），可以通过位置或关键字传递。
    e 和 f 是仅关键字参数（Keyword-Only Parameters），只能通过关键字传递。
    """
    sig = signature(as_query_func)  # 获取 as_query_func 的签名，sig包含了函数的参数列表及其相关信息
    sig = sig.replace(parameters=new_parameters)  # 修改签名，将其替换为新的参数列表
    # 将新的签名 sig 赋值给 as_query_func 的 __signature__ 属性，as_query_func 的签名被动态修改，以包含新的参数列表
    as_query_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_query', as_query_func)  # 将新定义的函数 as_query_func 作为 as_query 方法添加到类中，并返回这个类
    return cls


def as_form(cls: Type[BaseModel]):
    """
    pydantic模型表单参数装饰器，将pydantic模型用于接收表单参数
    """
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: FieldInfo  # type: ignore

        if not model_field.is_required():
            new_parameters.append(
                Parameter(
                    model_field.alias,
                    Parameter.POSITIONAL_ONLY,
                    default=Form(model_field.default),
                    annotation=model_field.annotation
                )
            )
        else:
            new_parameters.append(
                Parameter(
                    model_field.alias,
                    Parameter.POSITIONAL_ONLY,
                    default=Form(...),
                    annotation=model_field.annotation
                )
            )

    async def as_form_func(**data):
        return cls(**data)

    sig = signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, 'as_form', as_form_func)
    return cls
