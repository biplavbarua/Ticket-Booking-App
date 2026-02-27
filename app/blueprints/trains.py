"""Trains blueprint — search, PNR status, detail, and booking (JSON API)."""
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models import Train, Booking, Seat

trains_bp = Blueprint('trains', __name__)

@trains_bp.route('/', methods=['GET'])
def search_page():
    """Render the train search form."""
    return render_template('trains/search.html')


@trains_bp.route('/search', methods=['GET'])
def search():
    """Search trains by origin station, destination station, and date."""
    from datetime import datetime, timedelta

    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date = request.args.get('date', '')

    if not origin or not destination:
        flash('Please enter both origin and destination stations.', 'error')
        return redirect(url_for('trains.search_page'))

    base_query = Train.query.filter(
        func.lower(Train.origin).contains(origin.lower()),
        func.lower(Train.destination).contains(destination.lower()),
        Train.seats_available > 0,
    )

    search_date = None
    if date:
        try:
            search_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Use YYYY-MM-DD.', 'error')
            return redirect(url_for('trains.search_page'))

        query = base_query.filter(func.date(Train.departure) == search_date)
        trains = query.order_by(Train.departure.asc()).all()

        if not trains:
            date_from = search_date - timedelta(days=3)
            date_to = search_date + timedelta(days=3)
            query = base_query.filter(
                func.date(Train.departure) >= date_from,
                func.date(Train.departure) <= date_to,
            )
            trains = query.order_by(Train.departure.asc()).all()
            if trains:
                flash(f'No trains on {search_date.strftime("%b %d")}. Showing nearby dates.', 'info')
    else:
        trains = base_query.order_by(Train.departure.asc()).all()

    query_params = {'origin': origin, 'destination': destination, 'date': date}
    return render_template('trains/results.html', trains=trains, query=query_params)


@trains_bp.route('/pnr', methods=['GET'])
def pnr_status():
    """Check PNR status for an existing booking."""
    pnr_input = request.args.get('pnr', '').strip().upper()
    if pnr_input:
        booking = Booking.query.filter_by(pnr=pnr_input).first()
        if booking:
            return render_template('trains/pnr.html', booking=booking)
        else:
            flash(f'No booking found with PNR: {pnr_input}', 'error')
            return redirect(url_for('trains.search_page'))
            
    flash('Please enter a PNR number.', 'error')
    return redirect(url_for('trains.search_page'))


@trains_bp.route('/<int:train_id>', methods=['GET'])
def detail(train_id):
    """Show train details with class options."""
    train = Train.query.get_or_404(train_id)
    return render_template('trains/detail.html', train=train)


@trains_bp.route('/<int:train_id>/book', methods=['POST'])
@login_required
def book(train_id):
    """Create a train booking."""
    train = Train.query.get_or_404(train_id)
    
    travel_class = request.form.get('travel_class', 'SL')
    passenger_names = request.form.getlist('passenger_names[]')
    passenger_names = [n.strip() for n in passenger_names if n.strip()]
    num_passengers = len(passenger_names) if passenger_names else 1

    classes = train.get_classes()
    price_per = classes.get(travel_class, 0)
    if not price_per:
        flash('Invalid class selected.', 'error')
        return redirect(url_for('trains.detail', train_id=train.id))

    total_price = price_per * num_passengers

    # Atomic seat decrement to prevent race conditions
    result = db.session.execute(
        db.update(Train)
        .where(Train.id == train.id, Train.seats_available >= num_passengers)
        .values(seats_available=Train.seats_available - num_passengers)
    )
    if result.rowcount == 0:
        db.session.rollback()
        flash('Not enough seats available.', 'error')
        return redirect(url_for('trains.detail', train_id=train.id))

    # Handle seat selection
    seat_ids = request.form.getlist('seat_ids[]')
    seat_labels = []
    if seat_ids:
        seats = Seat.query.filter(
            Seat.id.in_([int(sid) for sid in seat_ids]),
            Seat.vehicle_type == 'train',
            Seat.vehicle_id == train.id,
            Seat.is_booked == False
        ).all()
        seat_labels = [s.seat_label for s in seats]

    booking = Booking(
        user_id=current_user.id,
        booking_type='train',
        ref_id=train.id,
        passenger_names=json.dumps(passenger_names),
        num_guests=num_passengers,
        travel_class=travel_class,
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
            Seat.vehicle_type == 'train',
            Seat.vehicle_id == train.id,
        ).update({Seat.is_booked: True, Seat.booking_id: booking.id}, synchronize_session=False)

    db.session.commit()

    flash('Booking created! Please complete payment.', 'success')
    return redirect(url_for('payment.checkout', booking_id=booking.id))
