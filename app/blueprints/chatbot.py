"""Chatbot blueprint — rule-based travel assistant."""
from flask import Blueprint, jsonify, request

chatbot_bp = Blueprint('chatbot', __name__)

# ── Knowledge Base ──
RESPONSES = {
    'greet': [
        "Hey there, fellow traveller! 🙌 How can I help you today?",
        "Welcome to Py-Booking! Ask me about travel tips, destinations, or bookings.",
    ],
    'budget': [
        "💰 **Budget Travel Tips:**\n"
        "• Book **early** — fares rise closer to departure\n"
        "• Travel **midweek** (Tue-Thu) for cheaper flights\n"
        "• Use our **Fare Calendar** to spot the cheapest dates\n"
        "• Consider **trains** for routes under 500km — great value!\n"
        "• Hotels near transit hubs are often cheaper",
    ],
    'destination_delhi': [
        "🏛️ **Delhi — The Capital City**\n"
        "• Must-see: Red Fort, Qutub Minar, India Gate, Humayun's Tomb\n"
        "• Food: Chandni Chowk street food (parathas, jalebi!)\n"
        "• Best time: Oct–Mar (pleasant weather)\n"
        "• Budget tip: Metro is the cheapest way to get around",
    ],
    'destination_mumbai': [
        "🌊 **Mumbai — City of Dreams**\n"
        "• Must-see: Gateway of India, Marine Drive, Elephanta Caves\n"
        "• Food: Vada Pav, Pav Bhaji at Juhu Beach\n"
        "• Best time: Nov–Feb (cool and dry)\n"
        "• Budget tip: Local trains are the lifeline — fast & cheap",
    ],
    'destination_goa': [
        "🏖️ **Goa — Beach Paradise**\n"
        "• Beaches: Palolem (south), Baga (north), Anjuna flea market\n"
        "• Food: Fish curry rice, bebinca\n"
        "• Best time: Nov–Feb\n"
        "• Budget tip: Rent a scooter, stay in hostels in South Goa",
    ],
    'destination_jaipur': [
        "🏰 **Jaipur — The Pink City**\n"
        "• Must-see: Amber Fort, Hawa Mahal, City Palace\n"
        "• Food: Dal Baati Churma, pyaaz kachori\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: Combo tickets save ₹200+ on monuments",
    ],
    'itinerary': [
        "📋 **Trip Planning Tips:**\n"
        "1. Pick your dates using our **Fare Calendar**\n"
        "2. Book transport first (flights/trains fill up fast)\n"
        "3. Hotels near city centre save travel time\n"
        "4. Keep 1 buffer day for unexpected plans\n"
        "5. Download offline maps before departure",
    ],
    'booking': [
        "🎫 **Booking Help:**\n"
        "• Search flights, trains, buses, or hotels from the homepage\n"
        "• Select your option and add passengers\n"
        "• Complete payment to get your PNR\n"
        "• View & manage all bookings in your **Profile Dashboard**\n"
        "• Cancel anytime from your trips page",
    ],
    'fallback': [
        "I can help with:\n"
        "• **Travel tips** — budget advice, packing lists\n"
        "• **Destinations** — Delhi, Mumbai, Goa, Jaipur\n"
        "• **Trip planning** — itinerary tips\n"
        "• **Bookings** — how to book, cancel, or find your PNR\n\n"
        "Just ask away! 🚀",
    ],
}

# ── Keyword → Category mapping ──
KEYWORDS = {
    'greet': ['hi', 'hello', 'hey', 'help', 'start', 'howdy'],
    'budget': ['budget', 'cheap', 'save', 'money', 'afford', 'cost', 'price', 'discount'],
    'destination_delhi': ['delhi', 'new delhi'],
    'destination_mumbai': ['mumbai', 'bombay'],
    'destination_goa': ['goa', 'beach'],
    'destination_jaipur': ['jaipur', 'rajasthan', 'pink city'],
    'itinerary': ['plan', 'itinerary', 'trip', 'schedule', 'route', 'travel plan'],
    'booking': ['book', 'cancel', 'pnr', 'payment', 'ticket', 'reservation', 'booking'],
}


def _match_intent(message):
    """Match user message to an intent category."""
    msg = message.lower().strip()
    for category, keywords in KEYWORDS.items():
        for kw in keywords:
            if kw in msg:
                return category
    return 'fallback'


@chatbot_bp.route('', methods=['POST'])
def chat():
    """Handle chat messages and return rule-based responses."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'message is required'}), 400

    intent = _match_intent(message)
    import random
    reply = random.choice(RESPONSES[intent])

    return jsonify({
        'reply': reply,
        'intent': intent,
    })
