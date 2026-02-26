"""Payment blueprint — mock payment checkout and confirmation (JSON API)."""
import random
import string
import time
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Booking, Flight, Train, Bus, Room

payment_bp = Blueprint('payment', __name__)

def _generate_pnr():
    """Generate a unique 8-character alphanumeric PNR."""
    while True:
        pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Booking.query.filter_by(pnr=pnr).first():
            return pnr


@payment_bp.route('/<int:booking_id>', methods=['GET'])
@login_required
def checkout(booking_id):
    """Return booking details for payment checkout."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('main.index'))

    if booking.status != 'Pending':
        flash('This booking has already been processed or cancelled.', 'warning')
        return redirect(url_for('auth.profile'))

    item_detail = _get_item_detail(booking)

    return render_template('payment/checkout.html', booking=booking, item_detail=item_detail)


@payment_bp.route('/<int:booking_id>/confirm', methods=['POST'])
@login_required
def confirm(booking_id):
    """Simulate successful payment — confirm booking and generate PNR."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
         flash('Unauthorized access.', 'error')
         return redirect(url_for('main.index'))

    if booking.status != 'Pending':
         flash('This booking has already been processed.', 'warning')
         return redirect(url_for('auth.profile'))

    # Simulate payment success
    booking.status = 'Confirmed'
    booking.pnr = _generate_pnr()
    db.session.commit()

    # --- Mock Email Confirmation ---
    item_detail = _get_item_detail(booking)
    from flask import current_app
    email_html = f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📧 BOOKING CONFIRMATION — Py-Booking
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    To: {current_user.email}
    Subject: Booking Confirmed — PNR {booking.pnr}

    Hi {current_user.username}! 🎉

    Your {booking.booking_type} booking is confirmed!

    PNR:    {booking.pnr}
    Type:   {booking.booking_type.capitalize()}
    Label:  {item_detail.get('label', 'N/A')}
    Route:  {item_detail.get('route', 'N/A')}
    Price:  ₹{booking.total_price:.2f}
    Guests: {booking.num_guests}

    Thank you for booking with Py-Booking!
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    current_app.logger.info(email_html)

    flash('Payment successful! Booking confirmed.', 'success')
    flash(f'Confirmation email sent to {current_user.email}', 'info')
    return render_template('payment/success.html', booking=booking)


def _get_item_detail(booking):
    """Fetch reference item details for a booking."""
    detail = {}
    if booking.booking_type == 'flight':
        item = Flight.query.get(booking.ref_id)
        if item:
            detail = {
                'label': f'{item.airline} {item.flight_number}',
                'route': f'{item.origin} → {item.destination}',
                'departure': item.departure.isoformat(),
                'arrival': item.arrival.isoformat(),
                'duration': item.duration_str(),
            }
    elif booking.booking_type == 'train':
        item = Train.query.get(booking.ref_id)
        if item:
            detail = {
                'label': f'{item.name} ({item.train_number})',
                'route': f'{item.origin} → {item.destination}',
                'departure': item.departure.isoformat(),
                'arrival': item.arrival.isoformat(),
                'duration': item.duration_str(),
                'class': booking.travel_class,
            }
    elif booking.booking_type == 'bus':
        item = Bus.query.get(booking.ref_id)
        if item:
            detail = {
                'label': f'{item.operator} ({item.bus_type})',
                'route': f'{item.origin} → {item.destination}',
                'departure': item.departure.isoformat(),
                'arrival': item.arrival.isoformat(),
                'duration': item.duration_str(),
            }
    elif booking.booking_type == 'hotel':
        room = Room.query.get(booking.ref_id)
        if room:
            detail = {
                'label': f'{room.hotel.name} — {room.room_type}',
                'route': room.hotel.city,
                'check_in': booking.check_in.isoformat() if booking.check_in else None,
                'check_out': booking.check_out.isoformat() if booking.check_out else None,
            }
    return detail
