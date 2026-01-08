from sqlalchemy import Column, String, JSON, BigInteger, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, nullable=False)
    username = Column(String, nullable=True)

    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    order_index = Column(Integer, nullable=True)
    meta_data = Column(JSON, nullable=True)

    room = relationship("Room", back_populates="players", lazy="selectin", foreign_keys=[room_id])

    __table_args__ = (Index("ix_users_room", "room_id"),)