import sqlalchemy
import re
import datetime
import jwt
from .db_session import SqlAlchemyBase
from werkzeug.security import generate_password_hash,  check_password_hash
import os
from errors import PasswordError

class User(SqlAlchemyBase):
    __tablename__ = "users"
    
    login = sqlalchemy.Column(sqlalchemy.String, primary_key=True, unique=True, index=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    countryCode = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    isPublic = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)
    phone = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def update_password(self, old_password, new_password):
        if not re.search(r"[A-Z]", new_password) or not re.search(r"[a-z]", new_password) or not re.search(r"[0-9]", new_password) or len(new_password) < 6 or len(new_password) > 100:
            raise PasswordError("Insecure password", 400)
        if check_password_hash(self.password, old_password):
            self.password = generate_password_hash(new_password)
            return True
        else:
            raise PasswordError("Invalid password", 403)

    
    def get_profile(self):
        result = {}
        result.update({
                "login": self.login,
                "email": self.email,
                "countryCode": self.countryCode,
                "isPublic": self.isPublic
            })
        if self.phone:
            result.update(phone=self.phone)
        if self.image:
            result.update(image=self.image)
        return result
    
    def update_profile(self, data):
        if "email" in data:
            self.email = data["email"]
        if "countryCode" in data:
            self.countryCode = data["countryCode"]
        if "phone" in data:
            self.phone = data["phone"]
        if "image" in data:
            self.image = data["image"]
        if "isPublic" in data:
            self.isPublic = data["isPublic"]
        
