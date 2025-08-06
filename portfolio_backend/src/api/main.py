from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse
from typing import List
from .models import (
    UserCreate, TokenResponse, UserInfo,
    PortfolioCreate, PortfolioUpdate, PortfolioResponse, StudentInfo
)
from .database import create_tables, get_db, User, Portfolio, PortfolioProject, PortfolioSkill, PortfolioAchievement
from .auth import (
    authenticate_user, get_password_hash, create_access_token, get_current_user
)
from sqlalchemy.orm import Session

# --- Meta for docs ---
tags_metadata = [
    {
        "name": "auth",
        "description": "User authentication (signup, login)",
    },
    {
        "name": "portfolios",
        "description": "Student portfolio CRUD operations",
    },
    {
        "name": "students",
        "description": "Student info endpoints",
    }
]

app = FastAPI(
    title="Student Portfolio Backend API",
    version="0.1.0",
    description="FastAPI backend for student portfolio builder app. Provides user authentication, portfolio CRUD, and student info endpoints.",
    openapi_tags=tags_metadata
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/", tags=["health"])
def health_check():
    """Health Check endpoint for the API."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post("/auth/signup", tags=["auth"], response_model=UserInfo, summary="Signup", description="Sign up a new user (student) by providing email and password.")
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    """Sign up a new user. Email must be unique."""
    user = db.query(User).filter(User.email == user_create.email).first()
    if user is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user_create.password)
    user = User(email=user_create.email, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserInfo(id=user.id, email=user.email)


# PUBLIC_INTERFACE
@app.post("/auth/login", tags=["auth"], response_model=TokenResponse, summary="Login", description="Obtain access token for authenticated routes.")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return TokenResponse(access_token=access_token)


# PUBLIC_INTERFACE
@app.get("/auth/me", tags=["auth"], response_model=UserInfo, summary="Get current user info")
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch logged-in user's public information"""
    return UserInfo(id=current_user.id, email=current_user.email)


# PUBLIC_INTERFACE
@app.post("/portfolios", tags=["portfolios"], response_model=PortfolioResponse, summary="Create a portfolio")
def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new portfolio for the logged-in student"""
    new_portfolio = Portfolio(
        student_id=current_user.id,
        title=portfolio.title,
        description=portfolio.description,
    )
    db.add(new_portfolio)
    db.commit()
    db.refresh(new_portfolio)

    # Save list relationships
    for p in (portfolio.projects or []):
        assoc = PortfolioProject(portfolio_id=new_portfolio.id, project=p)
        db.add(assoc)
    for s in (portfolio.skills or []):
        assoc = PortfolioSkill(portfolio_id=new_portfolio.id, skill=s)
        db.add(assoc)
    for a in (portfolio.achievements or []):
        assoc = PortfolioAchievement(portfolio_id=new_portfolio.id, achievement=a)
        db.add(assoc)
    db.commit()
    db.refresh(new_portfolio)
    return portfolio_to_response(new_portfolio, db)

# PUBLIC_INTERFACE
@app.get("/portfolios", tags=["portfolios"], response_model=List[PortfolioResponse], summary="List all my portfolios")
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolios = db.query(Portfolio).filter(Portfolio.student_id == current_user.id).all()
    return [portfolio_to_response(p, db) for p in portfolios]

# PUBLIC_INTERFACE
@app.get("/portfolios/{portfolio_id}", tags=["portfolios"], response_model=PortfolioResponse, summary="Get single portfolio")
def get_portfolio(
    portfolio_id: int = Path(..., description="ID of portfolio to fetch"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.student_id == current_user.id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio_to_response(portfolio, db)

# PUBLIC_INTERFACE
@app.put("/portfolios/{portfolio_id}", tags=["portfolios"], response_model=PortfolioResponse, summary="Update a portfolio")
def update_portfolio(
    portfolio_id: int,
    portfolio: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    obj = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.student_id == current_user.id).first()
    if obj is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    obj.title = portfolio.title
    obj.description = portfolio.description

    # Remove previous lists
    db.query(PortfolioProject).filter(PortfolioProject.portfolio_id == obj.id).delete()
    db.query(PortfolioSkill).filter(PortfolioSkill.portfolio_id == obj.id).delete()
    db.query(PortfolioAchievement).filter(PortfolioAchievement.portfolio_id == obj.id).delete()
    db.commit()
    # Add new associations
    for p in (portfolio.projects or []):
        assoc = PortfolioProject(portfolio_id=obj.id, project=p)
        db.add(assoc)
    for s in (portfolio.skills or []):
        assoc = PortfolioSkill(portfolio_id=obj.id, skill=s)
        db.add(assoc)
    for a in (portfolio.achievements or []):
        assoc = PortfolioAchievement(portfolio_id=obj.id, achievement=a)
        db.add(assoc)
    db.commit()
    db.refresh(obj)
    return portfolio_to_response(obj, db)

# PUBLIC_INTERFACE
@app.delete("/portfolios/{portfolio_id}", tags=["portfolios"], response_class=JSONResponse, summary="Delete a portfolio")
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.student_id == current_user.id).first()
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    return JSONResponse(content={"detail": "Portfolio deleted"})


# PUBLIC_INTERFACE
@app.get("/students", tags=["students"], response_model=List[StudentInfo], summary="List all students")
def list_students(db: Session = Depends(get_db)):
    """List all registered students and their portfolios."""
    users = db.query(User).all()
    out = []
    for user in users:
        out.append(student_info_for(user, db))
    return out

# PUBLIC_INTERFACE
@app.get("/students/{student_id}", tags=["students"], response_model=StudentInfo, summary="Get info for a specific student")
def get_student(student_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_info_for(user, db)

# --- Helper conversion functions ---

def portfolio_to_response(portfolio_obj, db):
    return PortfolioResponse(
        id=portfolio_obj.id,
        student_id=portfolio_obj.student_id,
        title=portfolio_obj.title,
        description=portfolio_obj.description,
        created_at=portfolio_obj.created_at,
        updated_at=portfolio_obj.updated_at,
        projects=[p.project for p in portfolio_obj.projects],
        skills=[s.skill for s in portfolio_obj.skills],
        achievements=[a.achievement for a in portfolio_obj.achievements]
    )

def student_info_for(user_obj, db):
    portfolios = db.query(Portfolio).filter(Portfolio.student_id == user_obj.id).all()
    return StudentInfo(
        id=user_obj.id,
        email=user_obj.email,
        portfolios=[portfolio_to_response(p, db) for p in portfolios]
    )
