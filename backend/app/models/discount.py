from sqlalchemy import create_engine, Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Discount(Base):
    __tablename__ = 'discounts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    percentage = Column(Float, nullable=False)
    conditions = Column(JSON, nullable=False)
    affected_products = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database setup
engine = create_engine('sqlite:///discounts.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)