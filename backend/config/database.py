from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
from config.env import DataBaseConfig

# quote_plus()会将斜线'/'编码为‘%2F’; 空格‘ ’编码为‘+’
# DATABASE_URL = <dialect>+<DBAPI>://<user>:<password>@<ip>:<port>/<schema>?<arg_key>=<value>&<arg_key>=<value>..
# mysql+pymysql://root:527644117@127.0.0.1:3306/eaviz
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DataBaseConfig.db_username}:{quote_plus(DataBaseConfig.db_password)}@" \
                          f"{DataBaseConfig.db_host}:{DataBaseConfig.db_port}/{DataBaseConfig.db_database}"

# 创建数据库引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=DataBaseConfig.db_echo,
    max_overflow=DataBaseConfig.db_max_overflow,
    pool_size=DataBaseConfig.db_pool_size,
    pool_recycle=DataBaseConfig.db_pool_recycle,
    pool_timeout=DataBaseConfig.db_pool_timeout
)

# 创建会话类负责实际的数据库操作（如添加、修改、查询等）
# autocommit=False 表示操作不会自动提交，需要手动调用 commit() 提交
# autoflush=False 表示不会在每次查询之前刷新未提交的对象
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建映射关系：返回一个基类，用于定义所有的数据模型（表的映射）
Base = declarative_base()
