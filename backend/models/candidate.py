"""
Candidate model
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from database import Base


class Candidate(Base):
    """Candidate model - stores hiring pipeline data"""
    
    __tablename__ = "candidates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.company_id"), nullable=False, index=True)
    
    # Candidate info
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    
    # Resume data
    resume_file_path = Column(String(500), nullable=True)
    resume_text = Column(Text, nullable=True)
    
    # Role info
    role_applied_for = Column(String(255), nullable=True, index=True)
    
    # AI Evaluation
    skills_extracted = Column(JSON, nullable=True)  # List of skills
    experience_depth = Column(String(50), nullable=True)
    execution_evidence = Column(Text, nullable=True)
    red_flags = Column(JSON, nullable=True)  # List of red flags
    fit_score = Column(Integer, nullable=True, index=True)  # 0-100
    
    # Summary
    executive_summary = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    gaps = Column(Text, nullable=True)
    
    # Verdict
    verdict = Column(String(50), nullable=True, index=True)  # Strong Yes/Maybe/Reject/Better fit elsewhere
    status = Column(String(50), default="screening", nullable=False, index=True)  # screening/shortlisted/interview/offer/rejected
    
    # Interview data
    interview_scheduled_at = Column(DateTime(timezone=True), nullable=True)
    interview_kit = Column(JSON, nullable=True)  # Questions, tasks, focus areas
    interview_feedback = Column(Text, nullable=True)
    
    # Metadata
    evaluation_metadata = Column(JSON, nullable=True)  # Full AI evaluation
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="candidates")
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, company_id={self.company_id}, name={self.name})>"

