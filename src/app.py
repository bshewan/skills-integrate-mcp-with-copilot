"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from pathlib import Path
import json
from typing import Optional
import bcrypt
import secrets
import uuid

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Load teacher credentials from teachers.json
def load_teachers():
    teachers_file = Path(__file__).parent / "teachers.json"
    try:
        with open(teachers_file, 'r') as f:
            data = json.load(f)
        return data.get("teachers", {})
    except FileNotFoundError:
        raise RuntimeError(
            f"Teacher credentials file not found at {teachers_file}. "
            "Please create a teachers.json file with teacher credentials."
        )
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Invalid JSON in teachers.json: {e}. "
            "Please ensure the file contains valid JSON with a 'teachers' object."
        )

# In-memory session storage (maps session tokens to teacher usernames)
# NOTE: This is a simple in-memory implementation suitable for single-process development only.
# In production, sessions should use:
# - A shared store (Redis, database) for multi-worker/multi-server deployments
# - Session expiration/TTL to prevent unbounded memory growth
# - Secure session token generation and storage
sessions = {}
teachers = load_teachers()

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/login")
def login(credentials: LoginRequest):
    """Authenticate a teacher and create a session"""
    if credentials.username not in teachers:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password using bcrypt
    stored_hash = teachers[credentials.username]
    
    try:
        if not bcrypt.checkpw(credentials.password.encode('utf-8'), stored_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except (ValueError, Exception):
        # If bcrypt fails (e.g., invalid hash format), reject authentication
        # This ensures only properly hashed passwords are accepted
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create a simple session token
    session_token = str(uuid.uuid4())
    sessions[session_token] = credentials.username
    
    return {"session_token": session_token, "username": credentials.username}


@app.post("/logout")
def logout(session_token: str):
    """Logout a teacher and destroy their session"""
    if session_token in sessions:
        del sessions[session_token]
        return {"message": "Logged out successfully"}
    raise HTTPException(status_code=401, detail="Invalid session")


@app.get("/auth/check")
def check_auth(session_token: Optional[str] = None):
    """Check if a user is authenticated"""
    if session_token and session_token in sessions:
        return {"authenticated": True, "username": sessions[session_token]}
    return {"authenticated": False}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, session_token: Optional[str] = None):
    """Sign up a student for an activity (requires teacher authentication)"""
    # Verify authentication
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Requires teacher login")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, session_token: Optional[str] = None):
    """Unregister a student from an activity (requires teacher authentication)"""
    # Verify authentication
    if not session_token or session_token not in sessions:
        raise HTTPException(status_code=401, detail="Requires teacher login")
    
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
