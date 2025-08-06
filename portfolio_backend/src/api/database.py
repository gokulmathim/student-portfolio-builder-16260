import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

import logging

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Please provide a valid value in your environment or .env file. "
        "See .env.example for guidance."
    )

try:
    engine = create_engine(DATABASE_URL, connect_args={})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception:
    # Print traceback for DB connection errors
    import sys, traceback
    print("FATAL ERROR: Could not connect to database with DATABASE_URL='%s'" % DATABASE_URL, file=sys.stderr)
    traceback.print_exc()
    logging.error("Could not connect to database at startup!", exc_info=True)
    raise

portfolio_projects_table = Table(
    "portfolio_projects",
    Base.metadata,
    Column("portfolio_id", Integer, ForeignKey("portfolios.id")),
    Column("project", String, nullable=False)
)

portfolio_skills_table = Table(
    "portfolio_skills",
    Base.metadata,
    Column("portfolio_id", Integer, ForeignKey("portfolios.id")),
    Column("skill", String, nullable=False)
)

portfolio_achievements_table = Table(
    "portfolio_achievements",
    Base.metadata,
    Column("portfolio_id", Integer, ForeignKey("portfolios.id")),
    Column("achievement", String, nullable=False)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    portfolios = relationship("Portfolio", back_populates="student", cascade="all, delete")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    projects = relationship(
        "PortfolioProject",
        back_populates="portfolio",
        cascade="all, delete, delete-orphan"
    )
    skills = relationship(
        "PortfolioSkill",
        back_populates="portfolio",
        cascade="all, delete, delete-orphan"
    )
    achievements = relationship(
        "PortfolioAchievement",
        back_populates="portfolio",
        cascade="all, delete, delete-orphan"
    )
    student = relationship("User", back_populates="portfolios")

class PortfolioProject(Base):
    __tablename__ = "portfolio_projects_assoc"
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    project = Column(String, nullable=False)
    portfolio = relationship("Portfolio", back_populates="projects")

class PortfolioSkill(Base):
    __tablename__ = "portfolio_skills_assoc"
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    skill = Column(String, nullable=False)
    portfolio = relationship("Portfolio", back_populates="skills")

class PortfolioAchievement(Base):
    __tablename__ = "portfolio_achievements_assoc"
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    achievement = Column(String, nullable=False)
    portfolio = relationship("Portfolio", back_populates="achievements")

def create_tables():
    Base.metadata.create_all(bind=engine)
