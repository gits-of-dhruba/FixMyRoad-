from sqlalchemy import Column, ForeignKey, Integer, String

from app.core.database import Base


class Authority(Base):
    __tablename__ = "authorities"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    road_type_id = Column(Integer, ForeignKey("road_types.id"), nullable=False)
    bbmp_division_id = Column(Integer, ForeignKey("bbmp_divisions.id"))
    escalation_to = Column(String(150))
    contact_email = Column(String(150))
    contact_phone = Column(String(15))
