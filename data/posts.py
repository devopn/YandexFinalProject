import sqlalchemy
import datetime
from .db_session import SqlAlchemyBase

class Post(SqlAlchemyBase):
    __tablename__ = "posts"
    
    id = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    author = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    tags = sqlalchemy.Column(sqlalchemy.ARRAY(sqlalchemy.String))

    createdAt = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=datetime.datetime.now)
        
    likesCount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=0)
    likersLogins = sqlalchemy.Column(sqlalchemy.ARRAY(sqlalchemy.String), default=[])

    dislikesCount = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=0)
    dislikersLogins = sqlalchemy.Column(sqlalchemy.ARRAY(sqlalchemy.String), default=[])        


    def get_post(self):
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author,
            "tags": self.tags,
            "createdAt": self.createdAt.isoformat(),
            "likesCount": self.likesCount,
            "dislikesCount": self.dislikesCount
        }