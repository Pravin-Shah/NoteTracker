from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import jwt
import httpx
from datetime import datetime, timedelta
import os
from api.database import execute_query, execute_insert, execute_update
from api.config import DATABASE_PATH

router = APIRouter(prefix="/api/auth", tags=["auth"])

# These should be in your .env
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

class GoogleLoginRequest(BaseModel):
    token: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/google")
async def google_login(request: GoogleLoginRequest):
    try:
        # Use the access token to get user info from Google
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {request.token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google access token")
            
            userinfo = response.json()
        
        # Extract user information
        google_id = userinfo['sub']
        email = userinfo['email']
        name = userinfo.get('name', '')
        picture = userinfo.get('picture', '')
        
        # Check if user exists
        users = execute_query("SELECT id FROM users WHERE google_id = ?", (google_id,))
        
        if users:
            user_id = users[0]['id']
            # Update avatar if changed
            execute_update("UPDATE users SET avatar_url = ? WHERE id = ?", (picture, user_id))
        else:
            # Check if user exists with this email (merge accounts)
            users_by_email = execute_query("SELECT id FROM users WHERE email = ?", (email,))
            if users_by_email:
                user_id = users_by_email[0]['id']
                execute_update("UPDATE users SET google_id = ?, avatar_url = ? WHERE id = ?", (google_id, picture, user_id))
            else:
                # Create new user
                user_id = execute_insert(
                    "INSERT INTO users (username, email, google_id, avatar_url, password_hash) VALUES (?, ?, ?, ?, ?)",
                    (email.split('@')[0], email, google_id, picture, "google-oauth")
                )
        
        # Create access token
        access_token = create_access_token(data={"sub": str(user_id), "email": email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
