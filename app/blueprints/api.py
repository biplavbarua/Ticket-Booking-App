"""API blueprint — JSON endpoints for autocomplete and lookups."""
from flask import Blueprint, jsonify, request
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
