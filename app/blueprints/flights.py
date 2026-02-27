"""Flights blueprint — search, detail, and booking (JSON API)."""
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Flight, Booking, Seat

flights_bp = Blueprint('flights', __name__)

@flights_bp.route('/', methods=['GET'])
def search_page():
    """Render the flight search form."""
    return render_template('flights/search.html')

@flights_bp.route('/search', methods=['GET'])
def search():
    """Search flights by origin, destination, and optional filters."""
    from datetime import datetime, timedelta
    from app.city_lookup import resolve_city_to_iata

    origin_raw = request.args.get('origin', '').strip()
    destination_raw = request.args.get('destination', '').strip()
    date = request.args.get('date', '')
    sort_by = request.args.get('sort', 'price')  # price or departure
    airline_filter = request.args.get('airline', '')

    if not origin_raw or not destination_raw:
        flash('Please enter both origin and destination.', 'error')
        return redirect(url_for('flights.search_page'))

    # Resolve city names → IATA codes
    origin = resolve_city_to_iata(origin_raw)
    destination = resolve_city_to_iata(destination_raw)

    base_query = Flight.query.filter(
        func.upper(Flight.origin) == origin,
        func.upper(Flight.destination) == destination,
        Flight.seats_available > 0,
    )

    # Filter by airline (applied to both exact and widened searches)
    if airline_filter:
        base_query = base_query.filter(Flight.airline.ilike(f'%{airline_filter}%'))

    search_date = None
    flexible = False

    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('flights.search_page'))

        # Exact date search first
        query = base_query.filter(func.date(Flight.departure) == search_date)
        flights = query.all()

        # Flexible fallback: widen to ±3 days if no exact match
        if not flights:
            date_from = search_date - timedelta(days=3)
            date_to = search_date + timedelta(days=3)
            query = base_query.filter(
                func.date(Flight.departure) >= date_from,
                func.date(Flight.departure) <= date_to,
            )
            flights = query.all()
            if flights:
                flexible = True
                flash(f'No flights on {search_date.strftime("%b %d")}. Showing nearby dates.', 'info')
    else:
        flights = base_query.all()

    # Sort
    if sort_by == 'departure':
        flights.sort(key=lambda f: f.departure)
    else:
        flights.sort(key=lambda f: f.price)

    query_params = {
        'origin': origin, 'destination': destination, 'date': date,
        'sort': sort_by, 'airline': airline_filter,
    }

    return render_template('flights/results.html', flights=flights, query=query_params)


@flights_bp.route('/<int:flight_id>', methods=['GET'])
def detail(flight_id):
    """Show flight details."""
    flight = Flight.query.get_or_404(flight_id)
    return render_template('flights/detail.html', flight=flight)


@flights_bp.route('/<int:flight_id>/book', methods=['POST'])
@login_required
def book(flight_id):
    """Create a flight booking."""
    flight = Flight.query.get_or_404(flight_id)
    
    passenger_names = request.form.getlist('passenger_names[]')
    passenger_names = [n.strip() for n in passenger_names if n.strip()]
    num_passengers = len(passenger_names) if passenger_names else 1

    total_price = flight.price * num_passengers

    # Atomic seat decrement to prevent race conditions
    result = db.session.execute(
        db.update(Flight)
        .where(Flight.id == flight.id, Flight.seats_available >= num_passengers)
        .values(seats_available=Flight.seats_available - num_passengers)
    )
    if result.rowcount == 0:
        db.session.rollback()
        flash('Not enough seats available.', 'error')
        return redirect(url_for('flights.detail', flight_id=flight.id))

    # Handle seat selection
    seat_ids = request.form.getlist('seat_ids[]')
    seat_labels = []
    if seat_ids:
        seats = Seat.query.filter(
            Seat.id.in_([int(sid) for sid in seat_ids]),
            Seat.vehicle_type == 'flight',
            Seat.vehicle_id == flight.id,
            Seat.is_booked == False
        ).all()
        seat_labels = [s.seat_label for s in seats]

    booking = Booking(
        user_id=current_user.id,
        booking_type='flight',
        ref_id=flight.id,
        passenger_names=json.dumps(passenger_names),
        num_guests=num_passengers,
        total_price=total_price,
        status='Pending',
        seat_numbers=json.dumps(seat_labels) if seat_labels else None,
    )
    db.session.add(booking)
    db.session.flush()

    # Mark seats as booked
    if seat_ids:
        Seat.query.filter(
            Seat.id.in_([int(sid) for sid in seat_ids]),
            Seat.vehicle_type == 'flight',
            Seat.vehicle_id == flight.id,
        ).update({Seat.is_booked: True, Seat.booking_id: booking.id}, synchronize_session=False)

    db.session.commit()

    flash('Booking created! Please complete payment.', 'success')
    return redirect(url_for('payment.checkout', booking_id=booking.id))
