import enum
from sqlalchemy import Column, BigInteger, String, Enum, Integer
from sqlalchemy.orm import relationship

from app.database.database import Base


class RoomStatus(enum.Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(BigInteger, nullable=False)
    status = Column(Enum(RoomStatus), nullable=False, default=RoomStatus.WAITING)

    current_truth_number = Column(Integer, nullable=False, default=1)
    current_action_number = Column(Integer, nullable=False, default=1)
    players_count = Column(Integer, nullable=False, default=0)

    current_turn_number = Column(Integer, nullable=False, default=1)

    invite_code = Column(String(16), nullable=False)

    players = relationship("User", back_populates="room", lazy="selectin", foreign_keys="User.room_id")