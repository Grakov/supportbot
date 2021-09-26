from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base
import config

engine = create_engine(f"mysql+pymysql://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}@" +
                       f"{config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DBNAME}?charset=utf8mb4", pool_pre_ping=True)
#engine.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_DBNAME} CHARACTER SET utf8mb4")
#engine.execute(f"USE {config.MYSQL_DBNAME}")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
db_session = Session()


def get_db_session():
    return Session()
