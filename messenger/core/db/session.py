from os import getenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

USER = getenv("POSTGRES_USER")
PASSWORD = getenv("POSTGRES_PASSWORD")
DB_PORT = getenv("DB_PORT")
DB_NAME = getenv("POSTGRES_DB")

db_url = "mysql+pymysql://python-messenger:f_GgpBNUnQanTveL@localhost:3306/python-messenger"
# sqllite_url = "sqlite://"
engine = create_engine(db_url)
session = sessionmaker(engine)
