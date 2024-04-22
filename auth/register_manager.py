import re
from data.users import User
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel, validator
from errors import RegisterError


class UserModel(BaseModel):
    login:str
    email:str
    password:str
    countryCode:str
    isPublic:bool
    phone:str|None = None
    image:str|None = None


    @validator("login")
    def login_check(cls, v):
        if not re.fullmatch(r"[a-zA-Z0-9-]+", v):
            raise RegisterError("Invalid login")
        if v in ["my"]:
            raise RegisterError("Incorrect login")
        if len(v) > 30 or len(v) < 1:
            raise RegisterError("Invalid login")
        return v
    
    @validator("email")
    def email_check(cls, v):
        if len(v) > 50 or not re.fullmatch(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", v):
            raise RegisterError("Invalid email")
        return v

    @validator("password")
    def password_check(cls, v):
        if len(v) < 6 or len(v) > 100:
            raise RegisterError("Password must be at least 6 characters long and no more than 100")
        if not re.search(r"[A-Z]", v) or not re.search(r"[a-z]", v) or not re.search(r"[0-9]", v):
            raise RegisterError("Password must contain at least one uppercase letter, one lowercase letter, and one digit")
        return v
    
    @validator("countryCode")
    def countryCode_check(cls, v):
        if not re.fullmatch(r"[a-zA-Z]{2}", v):
            raise RegisterError("Invalid country code. Code must be 2 letters")
        return v

    @validator("isPublic")
    def isPublic_check(cls, v):
        if not isinstance(v, bool):
            raise RegisterError("isPublic must be boolean")
        return v
    
    @validator("phone")
    def phone_check(cls, v):
        print(v)
        if v and (not re.fullmatch(r"\+[\d]+", v) or len(v) > 20):
            raise RegisterError("Invalid phone number")
        return v
    
    @validator("image")
    def image_check(cls, v):
        if v and len(v) > 200:
            raise RegisterError("Invalid image url")
        return v





class RegisterManager:
    def __init__(self, session: Session) -> None:
        self.session = session

    def register(self, input:dict):
        
        
        required_fields = ["login", "email", "password", "countryCode", "isPublic"]
        for field in required_fields:
            if input[field] is None:
                raise RegisterError(f"{field} is required", 400)
            
        cc = input.get("countryCode")
        if not isinstance(cc, str):
            raise RegisterError("Invalid country code", 400)
        
        try:
            data = UserModel(**input)
        except:
            raise RegisterError("Invalid data", 400)
        if data.phone: # if phone is null we don't need to check it
            a = self.session.query(User).filter(or_(User.login == data.login, User.email == data.email, User.phone == data.phone)).first()
        else:
            a = self.session.query(User).filter(or_(User.login == data.login, User.email == data.email)).first()

        if a:
            if a.login == data.login: 
                raise RegisterError("Login already exists", 409)
            if a.email == data.email:
                raise RegisterError("Email already exists", 409)
            if a.phone == data.phone:
                raise RegisterError("Phone already exists", 409)
                
        # Create user
        user = User(
            login = data.login,
            email = data.email,
            password = generate_password_hash(data.password),
            countryCode = data.countryCode,
            isPublic = data.isPublic,
            phone = data.phone,
            image = data.image
        )
        self.session.add(user)  
        self.session.commit()
        return user
        
    def validate_data(self, data:dict, user:User):
        # Check 
        email = data.get("email", user.email)
        countryCode = data.get("countryCode", user.countryCode)
        isPublic = data.get("isPublic", user.isPublic)
        if not isinstance(isPublic, bool):
            raise RegisterError("isPublic must be boolean", 400)
        result = UserModel(
            login=user.login,
            email=email if email else "",
            password="JustText_123",
            countryCode=countryCode if countryCode else "",
            isPublic= isPublic,
            phone=data.get("phone", user.phone),
            image=data.get("image", user.image)
        )
        if data.get("email", None):
            if self.session.query(User).filter(User.email == data.get("email")).first() and not (data.get("email") == user.email):
                # I checked that email is not used and it is not starting email of user
                raise RegisterError("email already used",409) 
        if data.get("phone", None):
            if self.session.query(User).filter(User.phone == data.get("phone")).first() and not (data.get("phone") == user.phone):
                # I checked that phone is not used and it is not starting phone of user
                raise RegisterError("phone already used",409)
        

            
        

