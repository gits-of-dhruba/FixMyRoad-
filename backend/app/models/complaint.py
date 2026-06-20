from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from sqlalchemy.orm import relationship

from app.core.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True)
    tracking_id = Column(String(20), nullable=False, unique=True)
    road_sl_no = Column(Integer, ForeignKey("roads.sl_no"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    authority_id = Column(Integer, ForeignKey("authorities.id"))
    issue_type = Column(String(30), nullable=False)
    severity = Column(String(10), nullable=False)
    confidence_score = Column(Numeric(5, 2))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    image_url = Column(Text)
    status = Column(String(20), nullable=False, default="Open")
    response_deadline = Column(DateTime)
    escalated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    resolved_at = Column(DateTime)

    road = relationship("Road", back_populates="complaints")
    user = relationship("User")
    authority = relationship("Authority")
