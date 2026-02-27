"""API blueprint — JSON endpoints for autocomplete, reviews, and fare calendar."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.city_lookup import search_cities

api_bp = Blueprint('api', __name__)


@api_bp.route('/cities', methods=['GET'])
def cities_autocomplete():
    """Return city suggestions for autocomplete.

    GET /api/cities?q=ahm  →  [{"city": "Ahmedabad", "code": "AMD"}, ...]
    """
    query = request.args.get('q', '').strip()
    results = search_cities(query)
    return jsonify(results)


# ── Reviews ──

@api_bp.route('/reviews', methods=['POST'])
@login_required
def create_review():
    """Create a review for a completed booking item."""
    from app.extensions import db
    from app.models import Review

    data = request.get_json(silent=True) or {}
    booking_type = data.get('booking_type', '').strip()
    ref_id = data.get('ref_id')
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if not booking_type or not ref_id or not rating:
        return jsonify({'error': 'booking_type, ref_id, and rating are required'}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': 'rating must be 1-5'}), 400

    existing = Review.query.filter_by(
        user_id=current_user.id, booking_type=booking_type, ref_id=ref_id
    ).first()
    if existing:
        return jsonify({'error': 'You have already reviewed this item'}), 409

    review = Review(
        user_id=current_user.id,
        booking_type=booking_type,
        ref_id=ref_id,
        rating=rating,
        comment=comment,
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.to_dict()), 201


@api_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """Get reviews for a specific item.

    GET /api/reviews?type=flight&ref_id=42
    """
    from app.models import Review
    from sqlalchemy import func

    booking_type = request.args.get('type', '').strip()
    ref_id = request.args.get('ref_id', type=int)

    if not booking_type or ref_id is None:
        return jsonify({'error': 'type and ref_id are required'}), 400

    reviews = Review.query.filter_by(booking_type=booking_type, ref_id=ref_id)\
        .order_by(Review.created_at.desc()).all()

    avg_q = Review.query.filter_by(booking_type=booking_type, ref_id=ref_id)\
        .with_entities(func.avg(Review.rating)).scalar()

    return jsonify({
        'reviews': [r.to_dict() for r in reviews],
        'count': len(reviews),
        'avg_rating': round(float(avg_q), 1) if avg_q else None,
    })


# ── Fare Calendar ──

@api_bp.route('/calendar', methods=['GET'])
def fare_calendar():
    """Return cheapest fare per day for a route+month.

    GET /api/calendar?type=flight&origin=DEL&destination=BOM&month=2026-03
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models import Flight, Train, Bus
    from app.city_lookup import resolve_city_to_iata

    btype = request.args.get('type', 'flight').strip().lower()
    origin_raw = request.args.get('origin', '').strip()
    dest_raw = request.args.get('destination', '').strip()
    month_str = request.args.get('month', '').strip()

    if not origin_raw or not dest_raw or not month_str:
        return jsonify({'error': 'origin, destination, and month are required'}), 400

    origin = resolve_city_to_iata(origin_raw)
    destination = resolve_city_to_iata(dest_raw)

    try:
        month_start = datetime.strptime(month_str, '%Y-%m').date()
    except ValueError:
        return jsonify({'error': 'month must be YYYY-MM format'}), 400

    # Calculate month's last day
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

    # Select model
    model_map = {'flight': Flight, 'train': Train, 'bus': Bus}
    Model = model_map.get(btype)
    if not Model:
        return jsonify({'error': 'type must be flight, train, or bus'}), 400

    # Flights use IATA codes; trains/buses store full station/city names
    if btype == 'flight':
        origin_filter = func.upper(Model.origin) == origin
        dest_filter = func.upper(Model.destination) == destination
    else:
        # Fuzzy match on city name for trains and buses
        origin_filter = func.lower(Model.origin).contains(origin_raw.lower())
        dest_filter = func.lower(Model.destination).contains(dest_raw.lower())

    results = Model.query.filter(
        origin_filter,
        dest_filter,
        func.date(Model.departure) >= month_start,
        func.date(Model.departure) <= month_end,
    ).all()

    # Group by day
    days = {}
    for item in results:
        day = item.departure.date().isoformat()
        if day not in days:
            days[day] = {'date': day, 'min_price': item.price, 'count': 0}
        days[day]['min_price'] = min(days[day]['min_price'], item.price)
        days[day]['count'] += 1

    return jsonify({
        'origin': origin,
        'destination': destination,
        'month': month_str,
        'type': btype,
        'days': sorted(days.values(), key=lambda d: d['date']),
    })
