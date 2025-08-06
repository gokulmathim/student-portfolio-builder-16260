from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for user creation request (signup)."""
    email: EmailStr = Field(..., description="User's email for signup/login")
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr = Field(..., description="User's email for login")
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class TokenResponse(BaseModel):
    """Schema for response containing JWT access token."""
    access_token: str
    token_type: str = "bearer"

# PUBLIC_INTERFACE
class UserInfo(BaseModel):
    """Schema for public user info (excludes password)."""
    id: int
    email: EmailStr

# PUBLIC_INTERFACE
class PortfolioBase(BaseModel):
    """Base schema for portfolio create/update."""
    title: str
    description: Optional[str] = ""
    projects: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    achievements: Optional[List[str]] = []

# PUBLIC_INTERFACE
class PortfolioCreate(PortfolioBase):
    pass

# PUBLIC_INTERFACE
class PortfolioUpdate(PortfolioBase):
    pass

# PUBLIC_INTERFACE
class PortfolioResponse(PortfolioBase):
    id: int
    student_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class StudentInfo(BaseModel):
    """Schema for listing/retrieving student info."""
    id: int
    email: EmailStr
    portfolios: Optional[List[PortfolioResponse]] = []
