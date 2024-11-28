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

# FCM send notification
fcm = FCMNotification(service_account_file="service_account_file.json", project_id="chatroom-ed57d")
# Create a new client and connect to the server
uri = ""
client = MongoClient(uri, server_api=ServerApi('1'))
db = client[""]
Users = db["Users"]
Cinemas = db["Cinemas"]
Messages = db["Messages"]
Videos = db["Videos"]
Tokens = db["Tokens"]
# define a Fast API app
app = FastAPI()

# register a new user
@app.post("/register_user")
async def register_user(request: Request):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# login
@app.post("/login_user")
async def register_user(request: Request):
    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))

# get the message of a user
@app.get("/get_user_message")
async def get_user_message(user_id: int):
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