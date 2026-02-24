"""City ↔ IATA code lookup for Indian airports and stations.

Used by the flights blueprint and the autocomplete API to resolve
user-friendly city names (e.g. 'Ahmedabad') to IATA codes (e.g. 'AMD').
"""

# ── City → IATA code mapping ─────────────────────────────────────────────
# Covers all cities in our seeded data plus ~20 more popular Indian cities.
CITY_TO_IATA = {
    # Seeded flight routes
    'Delhi': 'DEL',
    'New Delhi': 'DEL',
    'Mumbai': 'BOM',
    'Bombay': 'BOM',
    'Bangalore': 'BLR',
    'Bengaluru': 'BLR',
    'Kolkata': 'CCU',
    'Calcutta': 'CCU',
    'Hyderabad': 'HYD',
    'Chennai': 'MAA',
    'Madras': 'MAA',
    'Goa': 'GOI',

    # Extra popular cities
    'Ahmedabad': 'AMD',
    'Pune': 'PNQ',
    'Jaipur': 'JAI',
    'Lucknow': 'LKO',
    'Kochi': 'COK',
    'Cochin': 'COK',
    'Trivandrum': 'TRV',
    'Thiruvananthapuram': 'TRV',
    'Chandigarh': 'IXC',
    'Patna': 'PAT',
    'Bhopal': 'BHO',
    'Indore': 'IDR',
    'Nagpur': 'NAG',
    'Varanasi': 'VNS',
    'Srinagar': 'SXR',
    'Amritsar': 'ATQ',
    'Guwahati': 'GAU',
    'Udaipur': 'UDR',
    'Agra': 'AGR',
    'Coimbatore': 'CJB',
    'Visakhapatnam': 'VTZ',
    'Vizag': 'VTZ',
    'Bhubaneswar': 'BBI',
    'Ranchi': 'IXR',
    'Dehradun': 'DED',
    'Mangalore': 'IXE',
    'Vijayawada': 'VGA',
    'Raipur': 'RPR',
    'Madurai': 'IXM',
    'Leh': 'IXL',
    'Port Blair': 'IXZ',
    'Jodhpur': 'JDH',
}

# ── Reverse mapping: IATA → City ─────────────────────────────────────────
IATA_TO_CITY = {}
for city, code in CITY_TO_IATA.items():
    if code not in IATA_TO_CITY:
        IATA_TO_CITY[code] = city

# ── Station names used in trains / buses ─────────────────────────────────
STATION_ALIASES = {
    'NDLS': 'New Delhi',
    'BCT': 'Mumbai Central',
    'MMCT': 'Mumbai Central',
    'HWH': 'Howrah',
    'SDAH': 'Sealdah',
    'SBC': 'Bangalore',
    'MAS': 'Chennai',
    'SC': 'Hyderabad',
}


def resolve_city_to_iata(text: str) -> str:
    """Resolve a user input (city name or IATA code) to an IATA code.

    Returns the IATA code if found, otherwise returns the original text
    uppercased (so raw IATA codes still work).
    """
    text = text.strip()
    # Direct IATA code (2-4 uppercase letters)
    upper = text.upper()
    if upper in IATA_TO_CITY:
        return upper

    # City name lookup (case-insensitive)
    for city, code in CITY_TO_IATA.items():
        if city.lower() == text.lower():
            return code

    # Fallback: return uppercased (might be a raw code the user typed)
    return upper


def search_cities(query: str, limit: int = 8) -> list:
    """Return a list of matching cities for autocomplete.

    Each entry is a dict: {"city": "Ahmedabad", "code": "AMD"}
    """
    if not query or len(query) < 1:
        return []

    q = query.lower()
    results = []
    seen_codes = set()

    for city, code in CITY_TO_IATA.items():
        if city.lower().startswith(q) or code.lower().startswith(q):
            if code not in seen_codes:
                results.append({'city': city, 'code': code})
                seen_codes.add(code)
        if len(results) >= limit:
            break

    return results
