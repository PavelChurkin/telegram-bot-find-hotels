from sqlalchemy import Column, ForeignKey, Integer, String
from .base import Base
from sqlalchemy.orm import relationship


class History(Base):
    __tablename__ = 'History'
    uid = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    date_request = Column(String(100))
    selected_command = Column(String(100))
    city = Column(String(100))
    text = Column(String(7500))
    hotels = Column(String(7500))

# class Hotel(Base):
#     __tablename__ = 'Hotel'
#     id = Column(Integer, primary_key=True)
#     uid = Column(Integer, ForeignKey("History.uid"))
#     hotel_id = Column(Integer)
#     city = Column(String(100))
#     text = Column(String(7500))
#
#     history = relationship('History')
#
#
# class Photos(Base):
#     __tablename__ = 'Photo'
#     # id = Column(Integer, primary_key=True)
#     hotel_id = Column(Integer, ForeignKey("Hotel.hotel_id"), primary_key=True)
#     lst_photos = Column(String(7500))
#
#     hotel = relationship('Hotel')
