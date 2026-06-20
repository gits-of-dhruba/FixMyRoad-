from sqlalchemy import BigInteger, Column, Date, ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoadType(Base):
    __tablename__ = "road_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True)

    roads = relationship("Road", back_populates="road_type")


class BBMPDivision(Base):
    __tablename__ = "bbmp_divisions"

    id = Column(Integer, primary_key=True)
    name = Column(String(60), nullable=False, unique=True)

    roads = relationship("Road", back_populates="bbmp_division")


class Road(Base):
    __tablename__ = "roads"

    sl_no = Column(Integer, primary_key=True)
    road_id = Column(String(60), nullable=False)
    osm_id = Column(Text)
    road_name = Column(String(200), nullable=False)
    road_type_id = Column(Integer, ForeignKey("road_types.id"), nullable=False)
    road_ref = Column(String(20))
    length_km = Column(Numeric(8, 3), nullable=False)
    bbmp_division_id = Column(Integer, ForeignKey("bbmp_divisions.id"), nullable=False)
    contractor_name = Column(String(150), nullable=False)
    executive_engineer = Column(String(100), nullable=False)
    ee_contact = Column(BigInteger)
    asst_exec_engineer = Column(String(100))
    aee_contact = Column(BigInteger)
    asst_engineer = Column(String(100))
    ae_contact = Column(BigInteger)
    completion_date = Column(Date, nullable=False)
    dlp_period = Column(String(20), nullable=False)
    dlp_expiry_date = Column(Date, nullable=False)
    budget_sanctioned = Column(BigInteger, nullable=False)
    budget_released = Column(BigInteger, nullable=False)
    budget_spent = Column(BigInteger, nullable=False)
    budget_unspent = Column(BigInteger, nullable=False)
    health_score = Column(SmallInteger, nullable=False)
    last_complaint_date = Column(Date, nullable=False)
    open_complaints = Column(Integer, nullable=False, default=0)
    geometry = Column(Text)

    road_type = relationship("RoadType", back_populates="roads")
    bbmp_division = relationship("BBMPDivision", back_populates="roads")
    complaints = relationship("Complaint", back_populates="road")
    repairs = relationship("Repair", back_populates="road")
