from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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
import random
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
    
# # Dependency to get the current user from the token
# def get_current_user(token: str = Depends(verify_token)):
#     return token  # 返回解码后的JWT负载数据（如用户ID）
security = HTTPBearer()

# 自定义依赖，用于从Authorization头中提取Token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # 返回解码后的JWT负载
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid")

# test api
@app.get("/demo/")
async def get_demo(a: int = 0, b: int = 0, status_code=200):
  sum = a+b
  data = {"sum": sum, "date": datetime.utcnow()}
  return JSONResponse(content=jsonable_encoder(data))

# register a new user
@app.post("/api/auth/register_user")
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
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
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
@app.post("/api/auth/login_user")
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
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data=user_data, expires_delta=access_token_expires)

        response = {"status": "OK", "message": "Login successful", "access_token": access_token, "token_type": "bearer"}
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
@app.post("/api/rooms")
async def create_cinema(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        # get data from request
        data = await request.json()
        if "room_name" not in data.keys() or "video_url" not in data.keys():
            response = {"status": "ERROR", "message": "Missing required data"}
            return JSONResponse(content=jsonable_encoder(response), status_code=400)
       
        room_name = data["room_name"]
        video_url = data["video_url"]

        # Generate a unique 4-digit invitation code
        while True:
            invitation_code = str(random.randint(1000, 9999))
            existing_room = Cinemas.find_one({"invitation_code": invitation_code})
            if not existing_room:
                break

        # create a room
        new_room = {
            "room_name": room_name,
            "host_id": str(current_user["user_id"]),
            "video_url": video_url,
            "current_time": 0,
            "is_playing": False,
            "members": [],
            "invitation_code": invitation_code,  # 存储唯一的 4 位邀请码
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        result = Cinemas.insert_one(new_room)

        # create successfully
        response = {
            "room_id": str(result.inserted_id),
            "invitation_code": invitation_code,  # 返回邀请码给前端
            "message": "Room created successfully"
        }
        return JSONResponse(content=jsonable_encoder(response))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})

# get the list of cinema about key word
@app.get("/api/rooms")
async def get_cinema(keyword: str, current_user: dict = Depends(get_current_user)):
    try:
        # find the room with keyword
        query = {"room_name": {"$regex": keyword, "$options": "i"}}  # 不区分大小写匹配
        rooms = list(Cinemas.find(query))
        # get result
        result = []
        for room in rooms:
            result.append({
                "room_id": str(room["_id"]),
                "room_name": room["room_name"],
                "video_url": room["video_url"],
                "current_viewers": len(room.get("members", []))  # 使用 members 计算当前观看人数
            })
        # return result
        return JSONResponse(content=jsonable_encoder(result))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})


# join cinema
# @app.post("/api/rooms/{room_id}/join")
# async def join_cinema(room_id: str, current_user: dict = Depends(get_current_user)):
#     try:
#         # find the room
#         cinema = Cinemas.find_one({"_id": ObjectId(room_id)})
#         if not cinema:
#             raise HTTPException(status_code=404, detail="Room not found")
        
#         # check whether the user is already in the room
#         if str(current_user["user_id"]) in cinema.get("members", []):
#             return JSONResponse(content={"message": "You are already in this room"})
        
#         # add the user
#         Cinemas.update_one(
#             {"_id": ObjectId(room_id)},
#             {"$addToSet": {"members": str(current_user["user_id"])}}
#         )

#         # Joined room successfully
#         response = {"message": "Joined room successfully"}
#         return JSONResponse(content=jsonable_encoder(response))

#     except HTTPException as e:
#         return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})



# join cinema by invitation code
@app.post("/api/rooms/join_by_code")
async def join_cinema_by_code(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        # get data from request
        data = await request.json()
        if "invitation_code" not in data.keys():
            response = {"status": "ERROR", "message": "Missing required data"}
            return JSONResponse(content=jsonable_encoder(response), status_code=400)
        invitation_code = data["invitation_code"]
        
        # Find the room by invitation code
        cinema = Cinemas.find_one({"invitation_code": invitation_code})
        if not cinema:
            raise HTTPException(status_code=404, detail="Room not found with the given invitation code")
        
        # Check whether the user is already in the room
        if str(current_user["user_id"]) in cinema.get("members", []):
            return JSONResponse(content={"message": "You are already in this room"})

        # Add the user to the room
        Cinemas.update_one(
            {"_id": cinema["_id"]},
            {"$addToSet": {"members": str(current_user["user_id"])}}
        )

        # Joined room successfully
        response = {"message": "Joined room successfully using invitation code"}
        return JSONResponse(content=jsonable_encoder(response))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})


# send message
@app.post("/api/rooms/{room_id}/chat")
async def send_message(request: Request, room_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # get data from request
        data = await request.json()
        if "message" not in data.keys():
            raise HTTPException(status_code=400, detail="Missing required data")
        message_text = data["message"]

        # check whether room exist
        cinemas = list(Cinemas.find({}))
        room = Cinemas.find_one({"_id": room_id})
        for cinema in cinemas:
            if(str(cinema["_id"])=="674b6524ebd99552f81e9157"):
                room = cinema
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # check whether user in the room
        if str(current_user["user_id"]) not in room.get("members", []):
            raise HTTPException(status_code=403, detail="You are not a member of this room")

        # insert the message
        new_message = {
            "room_id": str(room_id),
            "user_id": str(current_user["user_id"]),
            "message": message_text,
            "sent_at": datetime.utcnow().isoformat()  # 使用 ISO 格式
        }
        result = Messages.insert_one(new_message)

        # # 使用 FCM 向房间中的其他用户发送通知（可选，需确保 FCM 配置正确）
        # if "members" in room:
        #     for member_id in room["members"]:
        #         if member_id != str(current_user["user_id"]):  # 不通知发送消息的用户自己
        #             user_token = Tokens.find_one({"user_id": member_id})
        #             if user_token:
        #                 fcm.notify_single_device(
        #                     registration_id=user_token["fcm_token"],
        #                     message_title=f"New message in {room['room_name']}",
        #                     message_body=message_text
        #                 )

        # Message sent successfully
        response = {
            "status": "OK",
            "response": "Message sent successfully",
            "message": message_text
        }
        return JSONResponse(content=jsonable_encoder(response))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})

# get messages
@app.get("/api/rooms/{room_id}/chat")
async def get_messages(room_id: str, current_user: dict = Depends(get_current_user)):
    try:
        # check whether room exists
        cinemas = list(Cinemas.find({}))
        room = Cinemas.find_one({"_id": room_id})
        for cinema in cinemas:
            if(str(cinema["_id"])=="674b6524ebd99552f81e9157"):
                room = cinema
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        # get message list
        messages = list(Messages.find({"room_id": room_id}))

        # change the form of message for sending
        formatted_messages = []
        for message in messages:
            user = Users.find_one({"_id": message["user_id"]})  
            # user not exist, skip
            if not user:
                continue  
            formatted_messages.append({
                "username": user["username"], 
                "message": message["message"], 
                "timestamp": message["sent_at"]  
            })

        # return list
        return JSONResponse(content=jsonable_encoder(formatted_messages))

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"status": "Error", "message": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "Error", "message": str(e)})
    

rooms = {}
# 创建WebSocket连接：用于同步视频播放状态
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, current_user: dict = Depends(get_current_user)):
    await websocket.accept()
    
    # 查找该房间
    room = Cinemas.find_one({"_id": room_id})
    if not room:
        await websocket.close(code=1000)
        return
    
    # 添加该用户到房间内的WebSocket列表
    if room_id not in rooms:
        rooms[room_id] = {}
    
    rooms[room_id][current_user["user_id"]] = websocket

    try:
        # 向房间中的所有用户广播消息
        await notify_room_members(room_id, {"status": "connected", "user": current_user["sub"]})
        
        # 监听来自客户端的播放控制消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 检查消息类型：播放控制（播放、暂停、进度更新）
            if "action" in message:
                action = message["action"]
                if action == "play":
                    # 广播播放消息给房间内所有成员
                    await broadcast_to_room(room_id, {"action": "play", "current_time": message.get("current_time")})
                elif action == "pause":
                    # 广播暂停消息给房间内所有成员
                    await broadcast_to_room(room_id, {"action": "pause", "current_time": message.get("current_time")})
                elif action == "seek":
                    # 广播跳转进度消息给房间内所有成员
                    await broadcast_to_room(room_id, {"action": "seek", "current_time": message.get("current_time")})

    except WebSocketDisconnect:
        # 如果用户断开连接，从房间的WebSocket列表中删除该用户
        del rooms[room_id][current_user["user_id"]]
        await notify_room_members(room_id, {"status": "disconnected", "user": current_user["sub"]})
        await websocket.close()

# 广播房间内的状态更新
async def broadcast_to_room(room_id: str, message: dict):
    for user_id, websocket in rooms.get(room_id, {}).items():
        await websocket.send_text(json.dumps(message))

# 广播消息给房间的所有成员
async def notify_room_members(room_id: str, message: dict):
    for user_id, websocket in rooms.get(room_id, {}).items():
        await websocket.send_text(json.dumps(message))