from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One-to-many relationship: One User has many Analyses
    analyses = relationship("Analysis", back_populates="user")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable=True so that older Phase 3 tests/records without users do not break DB rules
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    original_filename = Column(String, index=True)
    confidence_threshold = Column(Float)
    total_detections = Column(Integer)
    average_confidence = Column(Float)
    inference_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="analyses")
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"))
    
    # Class Info
    class_id = Column(Integer)
    class_name = Column(String)
    confidence = Column(Float)
    
    # Bounding Box coordinates (xyxy)
    x1 = Column(Float)
    y1 = Column(Float)
    x2 = Column(Float)
    y2 = Column(Float)
    
    # Pre-calculated geometry from Phase 1
    width = Column(Float)
    height = Column(Float)
    area = Column(Float)
    aspect_ratio = Column(Float)

    # Relationship back to the parent Analysis
    analysis = relationship("Analysis", back_populates="detections")
