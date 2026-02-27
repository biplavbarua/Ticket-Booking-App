"""SQLAlchemy models for the Travel Booking Platform.

Models:
  User       — registered users with hashed passwords
  Passenger  — saved traveller profiles linked to a user
  Flight     — flight inventory
  Train      — train inventory
  Bus        — bus inventory
  Hotel      — hotel properties
  Room       — room types within a hotel
  Booking    — unified booking ledger for all transport/hotel types
"""
from datetime import datetime, timezone
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


# ---------------------------------------------------------------------------
# User & Passenger
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    """Registered platform user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    passengers = db.relationship('Passenger', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class Passenger(db.Model):
    """Saved traveller profile for quick re-use during bookings."""
    __tablename__ = 'passengers'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # Male / Female / Other
    id_proof = db.Column(db.String(50))  # e.g. Aadhaar, Passport number

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'id_proof': self.id_proof
        }

    def __repr__(self):
        return f'<Passenger {self.name}>'


# ---------------------------------------------------------------------------
# Transport Models
# ---------------------------------------------------------------------------

class Flight(db.Model):
    """Flight inventory entry."""
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(10), nullable=False, index=True)
    airline = db.Column(db.String(80), nullable=False)
    origin = db.Column(db.String(10), nullable=False, index=True)       # Airport code
    destination = db.Column(db.String(10), nullable=False, index=True)   # Airport code
    departure = db.Column(db.DateTime, nullable=False)
    arrival = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    seats_available = db.Column(db.Integer, nullable=False, default=60)

    def duration_str(self):
        delta = self.arrival - self.departure
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f'{hours}h {minutes}m'

    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'airline': self.airline,
            'origin': self.origin,
            'destination': self.destination,
            'departure': self.departure.isoformat(),
            'arrival': self.arrival.isoformat(),
            'duration': self.duration_str(),
            'price': self.price,
            'seats_available': self.seats_available
        }

    def __repr__(self):
        return f'<Flight {self.flight_number} {self.origin}→{self.destination}>'


class Train(db.Model):
    """Train inventory entry."""
    __tablename__ = 'trains'

    id = db.Column(db.Integer, primary_key=True)
    train_number = db.Column(db.String(10), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    origin = db.Column(db.String(80), nullable=False, index=True)       # Station name
    destination = db.Column(db.String(80), nullable=False, index=True)   # Station name
    departure = db.Column(db.DateTime, nullable=False)
    arrival = db.Column(db.DateTime, nullable=False)
    classes = db.Column(db.Text, nullable=False, default='{}')
    seats_available = db.Column(db.Integer, nullable=False, default=120)

    def duration_str(self):
        delta = self.arrival - self.departure
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f'{hours}h {minutes}m'

    def get_classes(self):
        try:
            return json.loads(self.classes)
        except (json.JSONDecodeError, TypeError):
            return {}

    def to_dict(self):
        return {
            'id': self.id,
            'train_number': self.train_number,
            'name': self.name,
            'origin': self.origin,
            'destination': self.destination,
            'departure': self.departure.isoformat(),
            'arrival': self.arrival.isoformat(),
            'duration': self.duration_str(),
            'classes': self.get_classes(),
            'seats_available': self.seats_available
        }

    def __repr__(self):
        return f'<Train {self.train_number} {self.name}>'


class Bus(db.Model):
    """Bus inventory entry."""
    __tablename__ = 'buses'

    id = db.Column(db.Integer, primary_key=True)
    operator = db.Column(db.String(120), nullable=False)
    origin = db.Column(db.String(80), nullable=False, index=True)
    destination = db.Column(db.String(80), nullable=False, index=True)
    departure = db.Column(db.DateTime, nullable=False)
    arrival = db.Column(db.DateTime, nullable=False)
    bus_type = db.Column(db.String(30), nullable=False)  # Sleeper / Seater / Semi-Sleeper
    price = db.Column(db.Float, nullable=False)
    seats_available = db.Column(db.Integer, nullable=False, default=40)

    def duration_str(self):
        delta = self.arrival - self.departure
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f'{hours}h {minutes}m'

    def to_dict(self):
        return {
            'id': self.id,
            'operator': self.operator,
            'origin': self.origin,
            'destination': self.destination,
            'departure': self.departure.isoformat(),
            'arrival': self.arrival.isoformat(),
            'duration': self.duration_str(),
            'bus_type': self.bus_type,
            'price': self.price,
            'seats_available': self.seats_available
        }

    def __repr__(self):
        return f'<Bus {self.operator} {self.origin}→{self.destination}>'


# ---------------------------------------------------------------------------
# Hotel & Room
# ---------------------------------------------------------------------------

class Hotel(db.Model):
    """Hotel property listing."""
    __tablename__ = 'hotels'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(80), nullable=False, index=True)
    address = db.Column(db.String(250))
    star_rating = db.Column(db.Integer, default=3)  # 1-5
    description = db.Column(db.Text)

    rooms = db.relationship('Room', backref='hotel', lazy=True, cascade='all, delete-orphan')

    def min_price(self):
        if not self.rooms:
            return 0
        return min(r.price_per_night for r in self.rooms)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'address': self.address,
            'star_rating': self.star_rating,
            'description': self.description,
            'min_price': self.min_price(),
            'rooms': [r.to_dict() for r in self.rooms]
        }

    def __repr__(self):
        return f'<Hotel {self.name} ({self.city})>'


class Room(db.Model):
    """Room type within a hotel."""
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # Standard / Deluxe / Suite
    price_per_night = db.Column(db.Float, nullable=False)
    rooms_available = db.Column(db.Integer, nullable=False, default=10)

    def to_dict(self):
        return {
            'id': self.id,
            'room_type': self.room_type,
            'price_per_night': self.price_per_night,
            'rooms_available': self.rooms_available
        }

    def __repr__(self):
        return f'<Room {self.room_type} @ {self.hotel.name if self.hotel else "?"}>'


# ---------------------------------------------------------------------------
# Seat Map
# ---------------------------------------------------------------------------

class Seat(db.Model):
    """Individual seat within a flight, bus, or train."""
    __tablename__ = 'seats'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_type = db.Column(db.String(10), nullable=False, index=True)  # flight / bus / train
    vehicle_id = db.Column(db.Integer, nullable=False, index=True)
    seat_label = db.Column(db.String(10), nullable=False)  # e.g. '1A', '5D', 'LB-3'
    row = db.Column(db.Integer, nullable=False)
    col = db.Column(db.Integer, nullable=False)
    seat_class = db.Column(db.String(20), default='economy')
    is_booked = db.Column(db.Boolean, default=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)

    __table_args__ = (
        db.Index('ix_seat_vehicle', 'vehicle_type', 'vehicle_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'seat_label': self.seat_label,
            'row': self.row,
            'col': self.col,
            'seat_class': self.seat_class,
            'is_booked': self.is_booked,
        }

    def __repr__(self):
        return f'<Seat {self.seat_label} {self.vehicle_type}:{self.vehicle_id}>'


# ---------------------------------------------------------------------------
# Unified Booking Ledger
# ---------------------------------------------------------------------------

class Booking(db.Model):
    """Unified booking record — works for flights, trains, buses, and hotels."""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_type = db.Column(db.String(10), nullable=False)  # flight / train / bus / hotel
    ref_id = db.Column(db.Integer, nullable=False)            # FK to the specific item
    passenger_names = db.Column(db.Text)                      # JSON list of passenger names
    num_guests = db.Column(db.Integer, default=1)
    travel_class = db.Column(db.String(20))                   # For trains: SL/3A/2A/1A
    check_in = db.Column(db.Date)                             # For hotels
    check_out = db.Column(db.Date)                            # For hotels
    status = db.Column(db.String(20), default='Pending')      # Pending / Confirmed / Cancelled
    total_price = db.Column(db.Float, nullable=False)
    pnr = db.Column(db.String(10), unique=True, index=True)   # Generated on confirmation
    seat_numbers = db.Column(db.Text)                        # JSON list of assigned seat labels
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    seats = db.relationship('Seat', backref='booking', lazy=True)

    def get_seat_labels(self):
        try:
            return json.loads(self.seat_numbers) if self.seat_numbers else []
        except (json.JSONDecodeError, TypeError):
            return []

    def get_passengers(self):
        try:
            return json.loads(self.passenger_names) if self.passenger_names else []
        except (json.JSONDecodeError, TypeError):
            return []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'booking_type': self.booking_type,
            'ref_id': self.ref_id,
            'passenger_names': self.get_passengers(),
            'num_guests': self.num_guests,
            'travel_class': self.travel_class,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'status': self.status,
            'total_price': self.total_price,
            'pnr': self.pnr,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Booking #{self.id} {self.booking_type} — {self.status}>'


class Review(db.Model):
    """User review and rating for a completed booking."""
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_type = db.Column(db.String(10), nullable=False)   # flight / train / bus / hotel
    ref_id = db.Column(db.Integer, nullable=False)            # ID of the reviewed item
    rating = db.Column(db.Integer, nullable=False)            # 1-5
    comment = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='reviews')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'booking_type', 'ref_id', name='uq_user_review'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'booking_type': self.booking_type,
            'ref_id': self.ref_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Review #{self.id} {self.booking_type}:{self.ref_id} ★{self.rating}>'
