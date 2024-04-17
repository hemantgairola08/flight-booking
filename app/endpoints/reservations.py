from database import database
from fastapi import FastAPI, HTTPException, APIRouter
from models.models import ReservationModificationRequest
from models.models import ReservationRequest
from models.models import ReservationCancelRequest
from models.models import Reservation

app = FastAPI()

router = APIRouter(prefix="/flights/reserve", tags=["flights"])

# Endpoint to reserve a flight
@router.post("/", response_model=Reservation)
def reserve_flight(payload: ReservationRequest):
    conn, cursor = database.get_connection()
    flight_id = payload.flight_id
    user_id = payload.user_id

    cursor.execute("SELECT available_seats FROM flights WHERE id=?", (flight_id,))
    row = cursor.fetchone()
    print(row)
    if row is None:
        database.close_connection(conn)
        raise HTTPException(status_code=404, detail="Flight not found")

    # Check if there are available seats
    available_seats = row[0]
    print(available_seats)
    if available_seats <= 0:
        database.close_connection(conn)
        raise HTTPException(status_code=400, detail="No available seats for this flight")

    # Insert reservation into the database
    cursor.execute("INSERT INTO reservations (flight_id, user_id) VALUES (?, ?)",
                   (flight_id, user_id))
    reservation_id = cursor.lastrowid
    print(reservation_id)

    cursor.execute("UPDATE flights SET available_seats = ? WHERE id = ?",
                   (available_seats - 1, flight_id))

    conn.commit()
    database.close_connection(conn)

    return {"id": reservation_id, "flight_id": flight_id, "user_id": user_id}

# Endpoint to modify an existing flight reservation
@router.put("/modify", response_model=Reservation)
def modify_reservation(payload: ReservationModificationRequest):
    conn, cursor = database.get_connection()

    # Check if the reservation exists
    cursor.execute("SELECT * FROM reservations WHERE id=?", (payload.reservation_id,))
    row = cursor.fetchone()
    print(row)
    if row is None:
        database.close_connection(conn)
        raise HTTPException(status_code=404, detail="Reservation not found")

    old_flight_id = row[1]
    user_id = row[2]

    # Update reservation details
    cursor.execute("UPDATE reservations SET flight_id=? WHERE id=?",
                   (payload.new_flight_id,
                    payload.reservation_id))

    # Check if the flight has changed
    if old_flight_id != payload.new_flight_id:
        # Increase available seats for old flight
        cursor.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (old_flight_id,))
        # Decrease available seats for new flight
        cursor.execute("UPDATE flights SET available_seats = available_seats - 1 WHERE id = ?",
                       (payload.new_flight_id,))

    conn.commit()
    database.close_connection(conn)
    return {"id": payload.reservation_id, "flight_id": payload.new_flight_id, "user_id": user_id}


# Endpoint to cancel an existing flight reservation
@router.delete("/cancel")
def cancel_reservation(payload: ReservationCancelRequest):
    conn, cursor = database.get_connection()

    # Check if the reservation exists
    cursor.execute("SELECT flight_id FROM reservations WHERE id=?", (payload.reservation_id,))
    row = cursor.fetchone()
    print(row)
    if row is None:
        database.close_connection(conn)
        raise HTTPException(status_code=404, detail="Reservation not found")

    flight_id = row[0]

    # Delete the reservation from the database
    cursor.execute("DELETE FROM reservations WHERE id=?", (payload.reservation_id,))

    # Increase available seats for the canceled flight
    cursor.execute("UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?", (flight_id,))

    conn.commit()
    database.close_connection(conn)

    return {"message": "Reservation canceled successfully"}