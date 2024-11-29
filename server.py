from fastapi import FastAPI
from pymongo import MongoClient
from fastapi import HTTPException
from fastapi import Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from fastapi import Request
import json
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pyfcm import FCMNotification
from passlib.hash import bcrypt

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

# test api
@app.get("/demo/")
async def get_demo(a: int = 0, b: int = 0, status_code=200):
  sum = a+b
  data = {"sum": sum, "date": datetime.today()}
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
        # get data from request
        data = await request.json()
        if "username_or_email" not in data.keys() or "password" not in data.keys():
            response = {"status": "ERROR", "message": "Missing required data"}
            return JSONResponse(content=jsonable_encoder(response), status_code=400)
        username_or_email = data["username_or_email"]
        password = data["password"]

        # query users
        user = Users.find_one({
            "$or": [
                {"username": username_or_email},
                {"email": username_or_email}
            ]
        })
        # user not exist
        if not user:
            response = {"status": "ERROR", "message": "Invalid username/email"}
            return JSONResponse(content=jsonable_encoder(response), status_code=401)
        # password error
        if not bcrypt.verify(password, user["password_hash"]):
            response = {"status": "ERROR", "message": "Invalid password"}
            return JSONResponse(content=jsonable_encoder(response), status_code=401)
        
        # login successful
        response = {"status": "OK", "message": "Login successful"}
        return JSONResponse(content=jsonable_encoder(response))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})
    

# get the message of a user
@app.get("/get_user_message")
async def get_user_message(username: str):
    data = {"status": "OK"}
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