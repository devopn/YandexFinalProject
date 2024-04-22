import sqlalchemy
import datetime
from .db_session import SqlAlchemyBase

class Friends(SqlAlchemyBase):
    __tablename__ = "friends"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user1 = sqlalchemy.Column(sqlalchemy.String, index=True)
    user2 = sqlalchemy.Column(sqlalchemy.String)
    createdAt = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=datetime.datetime.now)
