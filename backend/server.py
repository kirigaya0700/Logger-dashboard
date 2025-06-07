from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, date
from passlib.context import CryptContext
from jose import JWTError, jwt
import pandas as pd
from io import StringIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    role: str  # "developer" or "manager"
    password_hash: str
    manager_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str
    manager_id: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    manager_id: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class Task(BaseModel):
    description: str
    time_spent: float  # hours
    completed: bool = True

class DailyLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: date
    tasks: List[Task]
    total_time: float
    mood: int  # 1-5 scale
    blockers: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DailyLogCreate(BaseModel):
    date: date
    tasks: List[Task]
    total_time: float
    mood: int
    blockers: Optional[str] = None

class DailyLogResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    date: date
    tasks: List[Task]
    total_time: float
    mood: int
    blockers: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    feedback: Optional[str] = None

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    log_id: str
    manager_id: str
    feedback_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackCreate(BaseModel):
    log_id: str
    feedback_text: str

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    type: str  # "reminder", "feedback", "info"
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise credentials_exception
    return User(**user)

# Authentication routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        password_hash=hashed_password,
        manager_id=user_data.manager_id
    )
    
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Create welcome notification
    welcome_notification = Notification(
        user_id=user.id,
        message=f"Welcome to DevLog, {user.username}! Start logging your daily work.",
        type="info"
    )
    await db.notifications.insert_one(welcome_notification.dict())
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user.dict())
    )

@api_router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user = await db.users.find_one({"username": login_data.username})
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(**user)
    )

# Daily log routes
@api_router.post("/logs", response_model=DailyLog)
async def create_daily_log(log_data: DailyLogCreate, current_user: User = Depends(get_current_user)):
    # Check if log already exists for this date
    existing_log = await db.daily_logs.find_one({"user_id": current_user.id, "date": log_data.date.isoformat()})
    if existing_log:
        raise HTTPException(status_code=400, detail="Log already exists for this date")
    
    # Create user
    daily_log = DailyLog(
        user_id=current_user.id,
        date=log_data.date,
        tasks=log_data.tasks,
        total_time=log_data.total_time,
        mood=log_data.mood,
        blockers=log_data.blockers
    )
    
    # Convert date to string for MongoDB storage
    log_dict = daily_log.dict()
    log_dict["date"] = log_data.date.isoformat()
    
    await db.daily_logs.insert_one(log_dict)
    
    # Notify manager if user has one
    if current_user.manager_id:
        manager_notification = Notification(
            user_id=current_user.manager_id,
            message=f"{current_user.username} submitted a daily log for {log_data.date}",
            type="info"
        )
        await db.notifications.insert_one(manager_notification.dict())
    
    return daily_log

@api_router.get("/logs", response_model=List[DailyLogResponse])
async def get_logs(current_user: User = Depends(get_current_user), start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {"user_id": current_user.id}
    
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" not in query:
            query["date"] = {}
        query["date"]["$lte"] = end_date
    
    logs = await db.daily_logs.find(query).sort("date", -1).to_list(1000)
    
    # Get feedback for each log
    result = []
    for log in logs:
        feedback = await db.feedback.find_one({"log_id": log["id"]})
        log_response = DailyLogResponse(
            **log,
            user_name=current_user.username,
            feedback=feedback["feedback_text"] if feedback else None
        )
        result.append(log_response)
    
    return result

@api_router.put("/logs/{log_id}", response_model=DailyLog)
async def update_daily_log(log_id: str, log_data: DailyLogCreate, current_user: User = Depends(get_current_user)):
    existing_log = await db.daily_logs.find_one({"id": log_id, "user_id": current_user.id})
    if not existing_log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    update_data = log_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.daily_logs.update_one({"id": log_id}, {"$set": update_data})
    
    updated_log = await db.daily_logs.find_one({"id": log_id})
    return DailyLog(**updated_log)

# Manager routes
@api_router.get("/team/logs", response_model=List[DailyLogResponse])
async def get_team_logs(current_user: User = Depends(get_current_user), start_date: Optional[str] = None, end_date: Optional[str] = None, developer_id: Optional[str] = None):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can view team logs")
    
    # Get developers under this manager
    developers = await db.users.find({"manager_id": current_user.id}).to_list(1000)
    developer_ids = [dev["id"] for dev in developers]
    
    query = {"user_id": {"$in": developer_ids}}
    
    if developer_id:
        query["user_id"] = developer_id
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" not in query:
            query["date"] = {}
        query["date"]["$lte"] = end_date
    
    logs = await db.daily_logs.find(query).sort("date", -1).to_list(1000)
    
    # Get user names and feedback
    result = []
    for log in logs:
        user = await db.users.find_one({"id": log["user_id"]})
        feedback = await db.feedback.find_one({"log_id": log["id"]})
        log_response = DailyLogResponse(
            **log,
            user_name=user["username"] if user else "Unknown",
            feedback=feedback["feedback_text"] if feedback else None
        )
        result.append(log_response)
    
    return result

@api_router.get("/team/developers", response_model=List[UserResponse])
async def get_team_developers(current_user: User = Depends(get_current_user)):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can view team developers")
    
    developers = await db.users.find({"manager_id": current_user.id}).to_list(1000)
    return [UserResponse(**dev) for dev in developers]

@api_router.post("/feedback", response_model=Feedback)
async def add_feedback(feedback_data: FeedbackCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="Only managers can add feedback")
    
    feedback = Feedback(
        log_id=feedback_data.log_id,
        manager_id=current_user.id,
        feedback_text=feedback_data.feedback_text
    )
    
    await db.feedback.insert_one(feedback.dict())
    
    # Get the log to find the developer
    log = await db.daily_logs.find_one({"id": feedback_data.log_id})
    if log:
        # Notify developer about feedback
        notification = Notification(
            user_id=log["user_id"],
            message=f"New feedback from {current_user.username} on your {log['date']} log",
            type="feedback"
        )
        await db.notifications.insert_one(notification.dict())
    
    return feedback

# Notification routes
@api_router.get("/notifications", response_model=List[Notification])
async def get_notifications(current_user: User = Depends(get_current_user)):
    notifications = await db.notifications.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
    return [Notification(**notif) for notif in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: User = Depends(get_current_user)):
    await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    return {"message": "Notification marked as read"}

# Analytics routes
@api_router.get("/analytics/productivity")
async def get_productivity_data(current_user: User = Depends(get_current_user), days: int = 30):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    query = {
        "user_id": current_user.id,
        "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
    }
    
    logs = await db.daily_logs.find(query).to_list(1000)
    
    # Create productivity data
    productivity_data = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        log = next((l for l in logs if l["date"] == current_date.isoformat()), None)
        productivity_data.append({
            "date": current_date.isoformat(),
            "total_time": log["total_time"] if log else 0,
            "mood": log["mood"] if log else 0,
            "tasks_count": len(log["tasks"]) if log else 0
        })
    
    return productivity_data

@api_router.get("/analytics/export")
async def export_productivity_data(start_date: str, end_date: str, current_user: User = Depends(get_current_user)):
    query = {
        "user_id": current_user.id,
        "date": {"$gte": start_date, "$lte": end_date}
    }
    
    logs = await db.daily_logs.find(query).sort("date", 1).to_list(1000)
    
    # Prepare data for CSV
    export_data = []
    for log in logs:
        for task in log["tasks"]:
            export_data.append({
                "Date": log["date"],
                "Task": task["description"],
                "Time Spent (hours)": task["time_spent"],
                "Completed": task["completed"],
                "Total Daily Time": log["total_time"],
                "Mood": log["mood"],
                "Blockers": log.get("blockers", "")
            })
    
    if not export_data:
        raise HTTPException(status_code=404, detail="No data found for the specified date range")
    
    # Create CSV
    df = pd.DataFrame(export_data)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    return {"csv_data": csv_content}

# Users list for manager assignment
@api_router.get("/users/managers", response_model=List[UserResponse])
async def get_managers():
    managers = await db.users.find({"role": "manager"}).to_list(1000)
    return [UserResponse(**manager) for manager in managers]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
