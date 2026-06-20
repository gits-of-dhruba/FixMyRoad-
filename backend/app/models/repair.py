from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Repair(Base):
    __tablename__ = "repairs"

    id = Column(Integer, primary_key=True)
    road_sl_no = Column(Integer, ForeignKey("roads.sl_no"), nullable=False)
    event_type = Column(String(20), nullable=False)
    event_date = Column(Date, nullable=False)
    notes = Column(Text)
    linked_complaint_id = Column(Integer, ForeignKey("complaints.id"))

    road = relationship("Road", back_populates="repairs")
