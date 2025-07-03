# Base class for declarative models SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, UniqueConstraint
)
from datetime import datetime


# Модель таблицы "cars" — содержит уникальную информацию об авто
class Car(Base):
    """
        Car model with all necessary fields (id, url of the card, title,
        seller name amd image url.)
    """

    __tablename__ = "cars"  # name of the table in database

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Reference on a car card
    url = Column(Text, unique=True, nullable=False)

    title = Column(String, nullable=False)

    # Seller name
    username = Column(String, nullable=True)

    # Reference on the photo
    image_url = Column(Text, nullable=True)


# Модель таблицы "listings" — конкретные зафиксированные цены, пробеги и т.д.
class AdsListing(Base):
    """
        AdsListing model describes all important data of the car.

    """

    # Table name in the database
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    car_id = Column(Integer, nullable=False)

    datetime_found = Column(DateTime, default=datetime.now, nullable=False)
    
    price_usd = Column(Float, nullable=True)
    
    odometer = Column(Float, nullable=True)
    
    phone_number = Column(String, nullable=True)
    
    car_number = Column(String, nullable=True)
    
    car_vin = Column(String, nullable=True)

    # Prohibit to save the same record of the car on the same date.
    __table_args__ = (UniqueConstraint("car_id", "datetime_found"),)
