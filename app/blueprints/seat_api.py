"""Seat map API — returns seat availability for a given vehicle."""
import json
from flask import Blueprint, jsonify
from app.extensions import db
from app.models import Seat

seat_api_bp = Blueprint('seat_api', __name__)


@seat_api_bp.route('/api/seats/<vehicle_type>/<int:vehicle_id>', methods=['GET'])
def get_seats(vehicle_type, vehicle_id):
    """Return all seats for a vehicle with their booking status."""
    if vehicle_type not in ('flight', 'bus', 'train'):
        return jsonify({'error': 'Invalid vehicle type'}), 400

    seats = Seat.query.filter_by(
        vehicle_type=vehicle_type,
        vehicle_id=vehicle_id
    ).order_by(Seat.row, Seat.col).all()

    return jsonify({
        'vehicle_type': vehicle_type,
        'vehicle_id': vehicle_id,
        'seats': [s.to_dict() for s in seats],
        'total': len(seats),
        'booked': sum(1 for s in seats if s.is_booked),
        'available': sum(1 for s in seats if not s.is_booked),
    })
