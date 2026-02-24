"""Hotels blueprint — search, detail, and room booking (JSON API)."""
import json
import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime
from app.extensions import db
from app.models import Hotel, Room, Booking

hotels_bp = Blueprint('hotels', __name__)

@hotels_bp.route('/', methods=['GET'])
def search_page():
    """Render the hotel search form."""
    return render_template('hotels/search.html')

@hotels_bp.route('/search', methods=['GET'])
def search():
    """Search hotels by city with check-in/check-out dates."""
    city = request.args.get('city', '').strip()
    check_in = request.args.get('check_in', '')
    check_out = request.args.get('check_out', '')
    star_filter = request.args.get('stars', '')

    if not city:
        flash('Please enter a city to search for hotels.', 'error')
        return redirect(url_for('hotels.search_page'))

    query = Hotel.query.filter(
        func.lower(Hotel.city).contains(city.lower())
    )

    if star_filter:
        try:
            query = query.filter(Hotel.star_rating >= int(star_filter))
        except ValueError:
            pass

    hotels = query.order_by(Hotel.star_rating.desc()).all()

    query_params = {
        'city': city, 'check_in': check_in, 'check_out': check_out, 'stars': star_filter,
    }
    
    return render_template('hotels/results.html', hotels=hotels, query=query_params)


@hotels_bp.route('/<int:hotel_id>', methods=['GET'])
def detail(hotel_id):
    """Show hotel details with available rooms."""
    hotel = Hotel.query.get_or_404(hotel_id)
    return render_template('hotels/detail.html', hotel=hotel)


@hotels_bp.route('/<int:hotel_id>/book', methods=['POST'])
@login_required
def book(hotel_id):
    """Create a hotel room booking."""
    hotel = Hotel.query.get_or_404(hotel_id)
    
    room_id = request.form.get('room_id')
    guest_name = request.form.get('guest_name', '').strip()
    check_in_str = request.form.get('check_in', '')
    check_out_str = request.form.get('check_out', '')

    try:
        room_id = int(room_id)
    except (ValueError, TypeError):
        flash('Invalid room ID.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    if not room_id or not check_in_str or not check_out_str:
        flash('Please fill in all required fields.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    room = Room.query.get_or_404(room_id)
    if room.hotel_id != hotel_id:
        flash('Invalid room selection.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    if room.rooms_available < 1:
        flash('This room type is fully booked.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    try:
        check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format. Use YYYY-MM-DD.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    if check_out_date <= check_in_date:
        flash('Check-out must be after check-in.', 'error')
        return redirect(url_for('hotels.detail', hotel_id=hotel.id))

    nights = (check_out_date - check_in_date).days
    total_price = room.price_per_night * nights
    import json
    
    booking = Booking(
        user_id=current_user.id,
        booking_type='hotel',
        ref_id=room.id,
        passenger_names=json.dumps([guest_name] if guest_name else [current_user.username]),
        num_guests=1,
        check_in=check_in_date,
        check_out=check_out_date,
        total_price=total_price,
        status='Pending',
    )

    room.rooms_available -= 1
    db.session.add(booking)
    db.session.commit()

    flash('Booking created! Please complete payment.', 'success')
    return redirect(url_for('payment.checkout', booking_id=booking.id))
