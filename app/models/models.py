from typing import Optional

from pydantic import BaseModel

class ReservationRequest(BaseModel):
    flight_id: int
    user_id: int

class ReservationModificationRequest(BaseModel):
    reservation_id: int
    new_flight_id: int

class ReservationCancelRequest(BaseModel):
    reservation_id: int

class Reservation(BaseModel):
    id: int
    flight_id: int
    user_id: int

class Flight(BaseModel):
    id: int
    origin: str
    destination: str
    departure_time: str
    capacity: int
    available_seats: int