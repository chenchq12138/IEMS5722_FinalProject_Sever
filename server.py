from fastapi import FastAPI
from pymongo import MongoClient
from fastapi import HTTPException
from fastapi import Form
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from fastapi import Request
import json
from datetime import timedelta, datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pyfcm import FCMNotification
from passlib.hash import bcrypt
import jwt
from typing import Optional

# JWT密钥和算法
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# FCM send notification
fcm = FCMNotification(service_account_file="service_account_file.json", project_id="chatroom-ed57d")
# Create a new client and connect to the server
uri = "mongodb+srv://chen:2744805546@chatroom.13sv1.mongodb.net/?retryWrites=true&w=majority&appName=Chatroom"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["IEMS5722_Final_Project"]
Users = db["Users"]
Cinemas = db["Cinemas"]
Messages = db["Messages"]
Videos = db["Videos"]
Tokens = db["Tokens"]
# define a Fast API app
app = FastAPI()

# Utility function to create JWT token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta  # 使用 timedelta 来计算过期时间
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)  # 默认过期时间60分钟
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Utility function to verify JWT token
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # 返回解码后的payload，其中包含了用户的信息
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")
    
# Dependency to get the current user from the token
def get_current_user(token: str = Depends(verify_token)):
    return token  # 返回解码后的JWT负载数据（如用户ID）

# test api
@app.get("/demo/")
async def get_demo(a: int = 0, b: int = 0, status_code=200):
  sum = a+b
  data = {"sum": sum, "date": datetime.utcnow()}
  return JSONResponse(content=jsonable_encoder(data))

# register a new user
@app.post("/register_user")
async def register_user(request: Request):
    try:
        # get data from request
        data = await request.json()
        if "username" not in data.keys() or "email" not in data.keys() or "password" not in data.keys():
            response = {"status": "ERROR", "message": "Missing required data"}
            return JSONResponse(content=jsonable_encoder(response), status_code=400)
        username = data["username"]
        email = data["email"]
        password = data["password"]

        # check whether username or email exists
        if Users.find_one({"username": username}):
            response = {"status": "ERROR", "message": "Username already exists"}
            return JSONResponse(content=jsonable_encoder(response), status_code=409)
        if Users.find_one({"email": email}):
            response = {"status": "ERROR", "message": "email already exists"}
            return JSONResponse(content=jsonable_encoder(response), status_code=409)

        # insert new user
        new_user = {
            "username": username,
            "password_hash": bcrypt.hash(password),
            "email": email,
            "avatar_url": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        Users.insert_one(new_user)

        # reponse
        response = {"status": "OK", "message": "User registered successfully"}
        return JSONResponse(content=jsonable_encoder(response))
    
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})
    

# login
@app.post("/login_user")
async def login_user(request: Request):
    try:
        data = await request.json()
        if "username_or_email" not in data or "password" not in data:
            return JSONResponse(status_code=400, content={"status": "ERROR", "message": "Missing required data"})

        username_or_email = data["username_or_email"]
        password = data["password"]

        user = Users.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })

        if not user:
            return JSONResponse(status_code=401, content={"status": "ERROR", "message": "Invalid username/email"})

        if not bcrypt.verify(password, user["password_hash"]):
            return JSONResponse(status_code=401, content={"status": "ERROR", "message": "Invalid password"})

        # JWT token data (you can include more user data here if necessary)
        user_data = {"sub": user["username"], "user_id": str(user["_id"])}
        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data=user_data, expires_delta=access_token_expires)

        response = {"status": "OK", "message": "Login successful", "access_token": access_token}
        return JSONResponse(content=jsonable_encoder(response))
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})

# Example of a protected route
@app.get("/protected_route")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user}

# Example of a user-specific route with JWT authentication
@app.get("/get_user_message")
async def get_user_message(username: str, current_user: dict = Depends(get_current_user)):
    # Here, you can use `current_user` to verify if the requesting user is authorized to access the messages
    if current_user["sub"] != username:
        raise HTTPException(status_code=403, detail="You are not authorized to access this data.")
    
    # Return the user's messages or other data
    data = {"status": "OK", "message": "This is the user's message data."}
    return JSONResponse(content=jsonable_encoder(data))

# create a new cinema
@app.post("/create_cinema")
async def create_cinema(request: Request):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# get the list of cinema about key word
@app.get("/get_cinema")
async def get_cinema(key_word: str):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# join cinema
@app.post("/join_cinema")
async def join_cinema(request: int):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# send message
@app.post("/send_message")
async def send_message(request: Request):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# get messages
@app.get("/get_messages")
async def get_messages(chatroom_id: int):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))