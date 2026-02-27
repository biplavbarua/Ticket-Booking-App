"""Ticket blueprint — printable ticket with QR code verification."""
import io
import json
import qrcode
from flask import Blueprint, render_template, request, send_file, abort, url_for
from flask_login import login_required, current_user
from app.models import Booking, Flight, Train, Bus, Room

ticket_bp = Blueprint('ticket', __name__)


def _get_booking_details(booking):
    """Build a detail dict for the ticket template."""
    detail = {
        'type': booking.booking_type.capitalize(),
        'pnr': booking.pnr,
        'passengers': json.loads(booking.passenger_names) if booking.passenger_names else [],
        'num_guests': booking.num_guests,
        'total_price': booking.total_price,
        'seats': json.loads(booking.seat_numbers) if booking.seat_numbers else [],
        'travel_class': booking.travel_class or '',
        'status': booking.status,
        'booked_at': booking.created_at,
    }

    if booking.booking_type == 'flight':
        item = Flight.query.get(booking.ref_id)
        if item:
            detail.update({
                'label': f'{item.airline} {item.flight_number}',
                'origin': item.origin,
                'destination': item.destination,
                'departure': item.departure,
                'arrival': item.arrival,
                'duration': item.duration_str(),
                'icon': 'fa-plane',
            })
    elif booking.booking_type == 'train':
        item = Train.query.get(booking.ref_id)
        if item:
            detail.update({
                'label': f'{item.name} #{item.train_number}',
                'origin': item.origin,
                'destination': item.destination,
                'departure': item.departure,
                'arrival': item.arrival,
                'duration': item.duration_str(),
                'icon': 'fa-train',
            })
    elif booking.booking_type == 'bus':
        item = Bus.query.get(booking.ref_id)
        if item:
            detail.update({
                'label': f'{item.operator} ({item.bus_type})',
                'origin': item.origin,
                'destination': item.destination,
                'departure': item.departure,
                'arrival': item.arrival,
                'duration': item.duration_str(),
                'icon': 'fa-bus',
            })
    elif booking.booking_type == 'hotel':
        room = Room.query.get(booking.ref_id)
        if room:
            detail.update({
                'label': f'{room.hotel.name} — {room.room_type}',
                'origin': room.hotel.city,
                'destination': '',
                'departure': booking.check_in,
                'arrival': booking.check_out,
                'duration': '',
                'icon': 'fa-hotel',
            })

    return detail


@ticket_bp.route('/ticket/<int:booking_id>')
@login_required
def view_ticket(booking_id):
    """Render a printable ticket page."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)
    if booking.status != 'Confirmed':
        abort(400, 'Booking is not confirmed yet.')

    detail = _get_booking_details(booking)
    qr_url = url_for('ticket.qr_code', booking_id=booking.id, _external=True)

    return render_template('ticket/ticket.html',
                           booking=booking, detail=detail, qr_url=qr_url,
                           user=current_user)


@ticket_bp.route('/ticket/<int:booking_id>/qr')
@login_required
def qr_code(booking_id):
    """Generate and serve a QR code PNG for booking verification."""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)

    # The QR encodes a verification URL
    verify_url = url_for('ticket.verify', pnr=booking.pnr, _external=True)

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
                        box_size=8, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color='#1e1b4b', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png', download_name=f'ticket_{booking.pnr}.png')


@ticket_bp.route('/verify/<pnr>')
def verify(pnr):
    """Public verification page — confirms ticket authenticity."""
    booking = Booking.query.filter_by(pnr=pnr).first()
    if not booking:
        return render_template('ticket/verify.html', booking=None, detail=None)

    detail = _get_booking_details(booking)
    return render_template('ticket/verify.html', booking=booking, detail=detail)
