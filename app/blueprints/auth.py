"""Auth blueprint — signup, login, logout, and user profile (JSON API)."""
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Booking, Flight, Train, Bus, Hotel, Room

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Register a new user account."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.signup'))
        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.signup'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('auth.signup'))
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
            return redirect(url_for('auth.signup'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.signup'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticate an existing user."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        flash('Invalid email or password.', 'error')
        
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """Return user profile with booking history."""
    bookings = Booking.query.filter_by(user_id=current_user.id)\
        .order_by(Booking.created_at.desc()).all()

    # Enrich bookings with reference details
    enriched = []
    for b in bookings:
        detail = {}
        if b.booking_type == 'flight':
            item = Flight.query.get(b.ref_id)
            if item:
                detail = {
                    'label': f'{item.airline} {item.flight_number}',
                    'route': f'{item.origin} → {item.destination}',
                    'date': item.departure.isoformat(),
                }
        elif b.booking_type == 'train':
            item = Train.query.get(b.ref_id)
            if item:
                detail = {
                    'label': f'{item.name} ({item.train_number})',
                    'route': f'{item.origin} → {item.destination}',
                    'date': item.departure.isoformat(),
                }
        elif b.booking_type == 'bus':
            item = Bus.query.get(b.ref_id)
            if item:
                detail = {
                    'label': item.operator,
                    'route': f'{item.origin} → {item.destination}',
                    'date': item.departure.isoformat(),
                }
        elif b.booking_type == 'hotel':
            room = Room.query.get(b.ref_id)
            if room:
                detail = {
                    'label': f'{room.hotel.name} — {room.room_type}',
                    'route': room.hotel.city,
                    'date': f'{b.check_in} to {b.check_out}' if b.check_in else 'N/A',
                }
        enriched.append({
            'booking': b, 
            'detail': detail
        })

    return render_template('auth/profile.html', user=current_user, bookings=enriched)


@auth_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a pending or confirmed booking."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('auth.profile'))

    if booking.status == 'Cancelled':
        flash('This booking is already cancelled.', 'error')
        return redirect(url_for('auth.profile'))
        
    booking.status = 'Cancelled'
    # Restore seat / room availability
    if booking.booking_type == 'flight':
        flight = Flight.query.get(booking.ref_id)
        if flight:
            flight.seats_available += booking.num_guests
    elif booking.booking_type == 'train':
        train = Train.query.get(booking.ref_id)
        if train:
            train.seats_available += booking.num_guests
    elif booking.booking_type == 'bus':
        bus = Bus.query.get(booking.ref_id)
        if bus:
            bus.seats_available += booking.num_guests
    elif booking.booking_type == 'hotel':
        room = Room.query.get(booking.ref_id)
        if room:
            room.rooms_available += 1

    db.session.commit()
    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('auth.profile'))
