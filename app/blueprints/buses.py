"""Buses blueprint — search, detail, and booking (JSON API)."""
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Bus, Booking, Seat

buses_bp = Blueprint('buses', __name__)

@buses_bp.route('/', methods=['GET'])
def search_page():
    """Render the bus search form."""
    return render_template('buses/search.html')


@buses_bp.route('/search', methods=['GET'])
def search():
    """Search buses by origin city, destination city, and optional type filter."""
    from datetime import datetime, timedelta

    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '')
    bus_type = request.args.get('bus_type', '')
    operator_filter = request.args.get('operator', '')

    if not origin or not destination:
        flash('Please enter both origin and destination cities.', 'error')
        return redirect(url_for('buses.search_page'))

    base_query = Bus.query.filter(
        func.lower(Bus.origin).contains(origin.lower()),
        func.lower(Bus.destination).contains(destination.lower()),
        Bus.seats_available > 0,
    )

    if bus_type:
        base_query = base_query.filter(func.lower(Bus.bus_type) == bus_type.lower())

    if operator_filter:
        base_query = base_query.filter(Bus.operator.ilike(f'%{operator_filter}%'))

    search_date = None
    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('buses.search_page'))

        query = base_query.filter(func.date(Bus.departure) == search_date)
        buses = query.order_by(Bus.price.asc()).all()

        if not buses:
            date_from = search_date - timedelta(days=3)
            date_to = search_date + timedelta(days=3)
            query = base_query.filter(
                func.date(Bus.departure) >= date_from,
                func.date(Bus.departure) <= date_to,
            )
            buses = query.order_by(Bus.price.asc()).all()
            if buses:
                flash(f'No buses on {search_date.strftime("%b %d")}. Showing nearby dates.', 'info')
    else:
        buses = base_query.order_by(Bus.price.asc()).all()

    query_params = {
        'origin': origin, 'destination': destination, 'date': date,
        'bus_type': bus_type, 'operator': operator_filter,
    }
    return render_template('buses/results.html', buses=buses, query=query_params)


@buses_bp.route('/<int:bus_id>', methods=['GET'])
def detail(bus_id):
    """Show bus details."""
    bus = Bus.query.get_or_404(bus_id)
    return render_template('buses/detail.html', bus=bus)


@buses_bp.route('/<int:bus_id>/book', methods=['POST'])
@login_required
def book(bus_id):
    """Create a bus booking."""
    bus = Bus.query.get_or_404(bus_id)
    
    passenger_names = request.form.getlist('passenger_names[]')
    passenger_names = [n.strip() for n in passenger_names if n.strip()]
    num_passengers = len(passenger_names) if passenger_names else 1

    if bus.seats_available < num_passengers:
        flash('Not enough seats available.', 'error')
        return redirect(url_for('buses.detail', bus_id=bus.id))

    total_price = bus.price * num_passengers

    # Atomic seat decrement to prevent race conditions
    result = db.session.execute(
        db.update(Bus)
        .where(Bus.id == bus.id, Bus.seats_available >= num_passengers)
        .values(seats_available=Bus.seats_available - num_passengers)
    )
    if result.rowcount == 0:
        db.session.rollback()
        flash('Not enough seats available.', 'error')
        return redirect(url_for('buses.detail', bus_id=bus.id))

    # Handle seat selection
    seat_ids = request.form.getlist('seat_ids[]')
    seat_labels = []
    if seat_ids:
        seats = Seat.query.filter(
            Seat.id.in_([int(sid) for sid in seat_ids]),
            Seat.vehicle_type == 'bus',
            Seat.vehicle_id == bus.id,
            Seat.is_booked == False
        ).all()
        seat_labels = [s.seat_label for s in seats]

    booking = Booking(
        user_id=current_user.id,
        booking_type='bus',
        ref_id=bus.id,
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
            Seat.vehicle_type == 'bus',
            Seat.vehicle_id == bus.id,
        ).update({Seat.is_booked: True, Seat.booking_id: booking.id}, synchronize_session=False)

    db.session.commit()

    flash('Booking created! Please complete payment.', 'success')
    return redirect(url_for('payment.checkout', booking_id=booking.id))
