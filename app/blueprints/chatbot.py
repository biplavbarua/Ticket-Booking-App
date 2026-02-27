"""Chatbot blueprint — smart rule-based travel assistant.

Uses scored keyword matching so specific intents (destinations) always
beat generic ones (greetings) even when both keywords appear.
"""
import random
from flask import Blueprint, jsonify, request

chatbot_bp = Blueprint('chatbot', __name__)

# ── Knowledge Base ──────────────────────────────────────────────────────
# Multiple response variants per category to avoid repetition.

RESPONSES = {
    # ── Greetings ──
    'greet': [
        "Hey there, fellow traveller! 🙌 How can I help you today?",
        "Welcome to Py-Booking! Ask me about travel tips, destinations, or bookings.",
        "Namaste! 🙏 Ready to plan your next adventure? Ask me anything!",
        "Hi! I'm your travel buddy. Try asking about a city, budget tips, or how to book!",
    ],

    # ── Budget ──
    'budget': [
        "💰 **Budget Travel Tips:**\n"
        "• Book **early** — fares rise closer to departure\n"
        "• Travel **midweek** (Tue-Thu) for cheaper flights\n"
        "• Use our **Fare Calendar** to spot the cheapest dates\n"
        "• Consider **trains** for routes under 500km — great value!\n"
        "• Hotels near transit hubs are often cheaper",

        "💰 **Save More on Travel:**\n"
        "• Sleeper buses are 40-60% cheaper than flights on short routes\n"
        "• Book **return tickets** together for combo discounts\n"
        "• Avoid peak season: Oct-Dec and Apr-Jun are cheaper to travel\n"
        "• Use our **Fare Calendar** — it shows the cheapest days!",

        "💰 **Budget Hacks:**\n"
        "• **Trains** beat flights on routes under 600km (and you see the countryside!)\n"
        "• Book hotels with free cancellation, then price-match later\n"
        "• Street food > restaurants — tastier AND cheaper\n"
        "• Travel overnight to save a night's hotel cost",
    ],

    # ── Destinations ──
    'destination_delhi': [
        "🏛️ **Delhi — The Capital City**\n"
        "• Must-see: Red Fort, Qutub Minar, India Gate, Humayun's Tomb\n"
        "• Food: Chandni Chowk street food (parathas, jalebi!)\n"
        "• Best time: Oct–Mar (pleasant weather)\n"
        "• Budget tip: Metro is the cheapest way to get around",

        "🏛️ **Delhi Highlights:**\n"
        "• History lovers: Mughal-era monuments are everywhere\n"
        "• Foodies: Old Delhi's Paranthe Wali Gali is legendary\n"
        "• Shopping: Sarojini Nagar for bargains, Khan Market for brands\n"
        "• Pro tip: Skip autos, use Delhi Metro — fast and ₹10-60 per trip",

        "🏛️ **Delhi Quick Guide:**\n"
        "• 3-day itinerary: Day 1 Old Delhi, Day 2 New Delhi monuments, Day 3 shopping\n"
        "• Don't miss: Lotus Temple (free entry!) and Akshardham\n"
        "• Getting around: Metro + Uber/Ola is the winning combo\n"
        "• Best street food: Chole Bhature at Sita Ram Diwan Chand",
    ],

    'destination_mumbai': [
        "🌊 **Mumbai — City of Dreams**\n"
        "• Must-see: Gateway of India, Marine Drive, Elephanta Caves\n"
        "• Food: Vada Pav, Pav Bhaji at Juhu Beach\n"
        "• Best time: Nov–Feb (cool and dry)\n"
        "• Budget tip: Local trains are the lifeline — fast & cheap",

        "🌊 **Mumbai Essentials:**\n"
        "• Nightlife: Bandra & Lower Parel have the best spots\n"
        "• Street food: Try Sev Puri and Bhel at Chowpatty Beach\n"
        "• Day trip: Elephanta Caves (₹20 ferry from Gateway)\n"
        "• Pro tip: Avoid rush hour trains (8-10 AM, 6-8 PM) unless you enjoy sardine life",

        "🌊 **Mumbai Insider Tips:**\n"
        "• Walk along Marine Drive at sunset — it's free and magical\n"
        "• Visit Dhobi Ghat for a unique Mumbai experience\n"
        "• Colaba Causeway is great for souvenirs and street shopping\n"
        "• Food must-try: Misal Pav and Bombay Sandwich",
    ],

    'destination_goa': [
        "🏖️ **Goa — Beach Paradise**\n"
        "• Beaches: Palolem (south), Baga (north), Anjuna flea market\n"
        "• Food: Fish curry rice, bebinca\n"
        "• Best time: Nov–Feb\n"
        "• Budget tip: Rent a scooter, stay in hostels in South Goa",

        "🏖️ **Goa Travel Guide:**\n"
        "• North Goa: Parties, nightlife, bustling beaches\n"
        "• South Goa: Quiet, scenic, better for couples\n"
        "• Must-try: Prawn Balchão and Feni (local cashew spirit)\n"
        "• Pro tip: Visit Dudhsagar Falls if you have an extra day",

        "🏖️ **Goa on a Budget:**\n"
        "• Stay in Arambol or Agonda for ₹500-800/night hostels\n"
        "• Rent a scooter for ₹300-400/day — the best way to explore\n"
        "• Eat at local 'shacks' (not the tourist ones on the beach)\n"
        "• Wednesday: Anjuna Flea Market for souvenirs & vibes",
    ],

    'destination_jaipur': [
        "🏰 **Jaipur — The Pink City**\n"
        "• Must-see: Amber Fort, Hawa Mahal, City Palace\n"
        "• Food: Dal Baati Churma, pyaaz kachori\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: Combo tickets save ₹200+ on monuments",

        "🏰 **Jaipur Highlights:**\n"
        "• Sunrise at Nahargarh Fort — stunning views of the Pink City\n"
        "• Shopping: Johari Bazaar for jewellery, Bapu Bazaar for textiles\n"
        "• Food: LMB (Laxmi Misthan Bhandar) is a Jaipur institution\n"
        "• Day trip: Ajmer & Pushkar are just 2 hours away",

        "🏰 **Jaipur Pro Tips:**\n"
        "• Buy the composite ticket (₹100) — covers 7 major monuments\n"
        "• Visit Amber Fort early morning to avoid crowds\n"
        "• The step-well at Chand Baori (Abhaneri) is 45 min away — worth it!\n"
        "• Best lassi: Lassiwala on MI Road (the original one)",
    ],

    'destination_bangalore': [
        "🌳 **Bangalore — The Garden City**\n"
        "• Must-see: Lalbagh Garden, Cubbon Park, Bangalore Palace\n"
        "• Food: Masala Dosa at MTR or Vidyarthi Bhavan\n"
        "• Best time: Year-round (pleasant climate!)\n"
        "• Budget tip: BMTC buses and Metro cover most spots",

        "🌳 **Bangalore Insider Guide:**\n"
        "• Craft beer capital of India — try breweries on 12th Main\n"
        "• Street food: VV Puram Food Street is a must-visit\n"
        "• Day trips: Nandi Hills (sunrise), Mysore (3 hours)\n"
        "• Pro tip: Traffic is legendary — plan Metro routes whenever possible",
    ],

    'destination_hyderabad': [
        "🕌 **Hyderabad — City of Pearls**\n"
        "• Must-see: Charminar, Golconda Fort, Ramoji Film City\n"
        "• Food: Hyderabadi Biryani (Paradise or Bawarchi), Haleem\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: MMTS trains are great for getting around cheaply",

        "🕌 **Hyderabad Highlights:**\n"
        "• Old City: Charminar, Laad Bazaar for bangles\n"
        "• HITEC City: Modern Hyderabad, great restaurants\n"
        "• Must-try: Irani Chai + Osmania biscuit combo\n"
        "• Day trip: Nagarjuna Sagar dam (3 hours)",
    ],

    'destination_chennai': [
        "🏖️ **Chennai — Gateway to the South**\n"
        "• Must-see: Marina Beach, Kapaleeshwarar Temple, Fort St. George\n"
        "• Food: Filter coffee, idli at Murugan Idli Shop, Chettinad cuisine\n"
        "• Best time: Nov–Feb (avoid Apr-Jun heat)\n"
        "• Budget tip: MTC buses are extensive and super cheap",

        "🏖️ **Chennai Insider Tips:**\n"
        "• Visit Mahabalipuram (1 hour) for UNESCO shore temples\n"
        "• T. Nagar is Chennai's shopping mecca (silk sarees!)\n"
        "• Must-try: Kothu Parotta and Jigarthanda\n"
        "• Pro tip: Learn to say 'Vanakkam' — locals love it!",
    ],

    'destination_kolkata': [
        "🌉 **Kolkata — City of Joy**\n"
        "• Must-see: Victoria Memorial, Howrah Bridge, Indian Museum\n"
        "• Food: Rosogolla, Kathi Roll (Nizam's), Mishti Doi\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: Yellow taxis and trams are part of the experience",

        "🌉 **Kolkata Highlights:**\n"
        "• Book lover? College Street has the largest book market in India\n"
        "• Park Street for food: Peter Cat (Chelo Kebab) is legendary\n"
        "• Don't miss: Kumartuli — watch artisans sculpt idols\n"
        "• Pro tip: Evening walk along the Hooghly River is magical",
    ],

    'destination_varanasi': [
        "🛕 **Varanasi — The Spiritual Capital**\n"
        "• Must-see: Ganga Aarti at Dashashwamedh Ghat, Kashi Vishwanath Temple\n"
        "• Food: Banarasi Paan, Tamatar Chaat, Lassi at Blue Lassi Shop\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: Walk the ghats — the best experience is free",

        "🛕 **Varanasi Guide:**\n"
        "• Sunrise boat ride on the Ganges — ₹100-200 shared boat\n"
        "• Explore the narrow lanes (galis) of the old city on foot\n"
        "• Sarnath (Buddha's first sermon) is just 10 km away\n"
        "• Pro tip: Photography at Manikarnika Ghat is not allowed — please respect",
    ],

    'destination_udaipur': [
        "🏰 **Udaipur — City of Lakes**\n"
        "• Must-see: City Palace, Lake Pichola, Jag Mandir\n"
        "• Food: Dal Baati Churma, Gatte ki Sabzi\n"
        "• Best time: Sep–Mar\n"
        "• Budget tip: Rooftop restaurants overlooking the lake are surprisingly affordable",

        "🏰 **Udaipur Insider Tips:**\n"
        "• Sunset from Sajjangarh (Monsoon Palace) is unforgettable\n"
        "• Boat ride on Lake Pichola — ₹400, totally worth it\n"
        "• Explore Haldighati if you're into history\n"
        "• Pro tip: Stay near Gangaur Ghat for the best lake views on a budget",
    ],

    'destination_agra': [
        "🕌 **Agra — Home of the Taj Mahal**\n"
        "• Must-see: Taj Mahal (sunrise!), Agra Fort, Fatehpur Sikri\n"
        "• Food: Petha (sweet), Bedai-Jalebi for breakfast\n"
        "• Best time: Oct–Mar\n"
        "• Budget tip: Skip guides at the gate, use an audio guide app",

        "🕌 **Agra Quick Guide:**\n"
        "• Visit Taj at sunrise — fewer crowds, golden light, magical\n"
        "• Mehtab Bagh across the river gives a stunning Taj view (₹50)\n"
        "• Fatehpur Sikri is 40 km away and worth the half-day trip\n"
        "• Pro tip: Fridays the Taj is closed!",
    ],

    'destination_kerala': [
        "🌴 **Kerala — God's Own Country**\n"
        "• Must-see: Alleppey backwaters, Munnar tea gardens, Fort Kochi\n"
        "• Food: Appam & Stew, Kerala Fish Curry, Puttu & Kadala\n"
        "• Best time: Sep–Mar\n"
        "• Budget tip: Government houseboats are cheaper than private ones",

        "🌴 **Kerala Highlights:**\n"
        "• Alleppey: Houseboat cruise through the backwaters\n"
        "• Munnar: Tea plantations, Eravikulam National Park\n"
        "• Varkala: Cliff beach — Goa vibes without the crowds\n"
        "• Pro tip: Try a Kathakali dance performance in Fort Kochi",
    ],

    # ── Generic Intents ──
    'itinerary': [
        "📋 **Trip Planning Tips:**\n"
        "1. Pick your dates using our **Fare Calendar**\n"
        "2. Book transport first (flights/trains fill up fast)\n"
        "3. Hotels near city centre save travel time\n"
        "4. Keep 1 buffer day for unexpected plans\n"
        "5. Download offline maps before departure",

        "📋 **Planning Checklist:**\n"
        "1. Decide dates → check our **Fare Calendar** for cheapest days\n"
        "2. Book flights/trains early — prices only go up\n"
        "3. Hotels: book refundable, re-check prices closer to trip\n"
        "4. Pack light — Indian airlines are strict on luggage\n"
        "5. Keep digital copies of all IDs",

        "📋 **Smart Travel Planning:**\n"
        "1. Start with transport — that's the biggest expense\n"
        "2. Use our search to compare flights vs trains vs buses\n"
        "3. For multi-city: Delhi → Agra → Jaipur is the classic Golden Triangle\n"
        "4. Always have a backup plan for delays\n"
        "5. Download UPI apps for cashless payments everywhere",
    ],

    'booking': [
        "🎫 **Booking Help:**\n"
        "• Search flights, trains, buses, or hotels from the homepage\n"
        "• Select your option and add passengers\n"
        "• Complete payment to get your PNR\n"
        "• View & manage all bookings in your **Profile Dashboard**\n"
        "• Cancel anytime from your trips page",

        "🎫 **How to Book:**\n"
        "1. Use the search tabs on the homepage (Flights/Trains/Buses/Hotels)\n"
        "2. Pick your option from the results\n"
        "3. Add passenger names and confirm\n"
        "4. Complete the payment → you'll get a unique PNR\n"
        "5. All bookings are saved in your **Profile**",

        "🎫 **Booking FAQ:**\n"
        "• **Cancel?** Go to Profile → click Cancel on any booking\n"
        "• **PNR status?** Check it on the Trains page\n"
        "• **Multiple passengers?** Add them on the detail page before booking\n"
        "• **Payment failed?** The booking stays as 'Pending' — retry from your Profile",
    ],

    'weather': [
        "🌤️ **Best Travel Seasons in India:**\n"
        "• **Oct–Mar**: North India (Delhi, Jaipur, Agra, Varanasi)\n"
        "• **Nov–Feb**: South India, Goa, Mumbai\n"
        "• **Sep–Mar**: Kerala, Udaipur\n"
        "• **Apr–Jun**: Hill stations (Shimla, Manali, Darjeeling)\n"
        "• **Jul–Sep**: Monsoon — Meghalaya, Coorg, Western Ghats",

        "🌤️ **Weather Tips:**\n"
        "• Carry sunscreen year-round — Indian sun is no joke\n"
        "• Monsoon (Jul-Sep): Beautiful but carry rain gear\n"
        "• Winter (Nov-Feb): Light jacket for North, comfortable in South\n"
        "• Summer (Apr-Jun): Stick to hill stations and beaches",
    ],

    'food': [
        "🍛 **Must-Try Indian Food by Region:**\n"
        "• **North**: Butter Chicken, Chole Bhature, Parathas\n"
        "• **South**: Masala Dosa, Hyderabadi Biryani, Filter Coffee\n"
        "• **West**: Vada Pav, Dhokla, Goan Fish Curry\n"
        "• **East**: Rosogolla, Momos, Litti Chokha\n"
        "• Street food is often the best food — be adventurous!",

        "🍛 **Foodie Travel Tips:**\n"
        "• Always eat where locals are eating — that's the quality seal\n"
        "• Delhi's Chandni Chowk has the best street food in India\n"
        "• Hyderabad for Biryani, Kolkata for sweets, Mumbai for Chaat\n"
        "• Carry antacids if you plan to go all-in on street food 😄",
    ],

    'safety': [
        "🛡️ **India Travel Safety Tips:**\n"
        "• Keep digital copies of your passport/ID on your phone\n"
        "• Use official taxis (Ola/Uber) over random autos\n"
        "• Drink bottled water, avoid ice from unknown sources\n"
        "• Keep emergency numbers: Police 100, Ambulance 108\n"
        "• Trust your instincts — most people are genuinely helpful",
    ],

    'thanks': [
        "You're welcome! 😊 Have an amazing trip!",
        "Happy to help! 🚀 Safe travels!",
        "Anytime! Let me know if you need anything else. ✈️",
        "Glad I could help! Enjoy your journey! 🌍",
    ],

    # ── Fallback ──
    'fallback': [
        "I can help with:\n"
        "• **Destinations** — Delhi, Mumbai, Goa, Jaipur, Bangalore, Hyderabad, and more\n"
        "• **Budget tips** — save money on travel\n"
        "• **Trip planning** — itinerary and weather advice\n"
        "• **Bookings** — how to book, cancel, or find your PNR\n"
        "• **Food & Safety** — what to eat and travel precautions\n\n"
        "Just ask away! 🚀",

        "Hmm, I didn't quite get that. Try asking about:\n"
        "• A city (e.g. \"Tell me about Goa\")\n"
        "• Budget tips (e.g. \"How to save on flights\")\n"
        "• Booking help (e.g. \"How do I cancel a booking\")\n"
        "• Food or weather tips\n\n"
        "I'm here to help! 😊",

        "I'm not sure about that, but here's what I know:\n"
        "• 🏙️ City guides for 12+ Indian destinations\n"
        "• 💰 Budget travel strategies\n"
        "• 📋 Trip planning checklists\n"
        "• 🎫 Booking & cancellation help\n\n"
        "Try asking about any of these!",
    ],
}


# ── Keyword → Category mapping with priority weights ────────────────────
# Higher weight = higher priority. Destination keywords beat generic ones.

KEYWORDS = {
    # --- High priority (weight 10): Destinations ---
    'destination_delhi':     {'weight': 10, 'keywords': ['delhi', 'new delhi', 'red fort', 'india gate', 'qutub minar', 'chandni chowk']},
    'destination_mumbai':    {'weight': 10, 'keywords': ['mumbai', 'bombay', 'marine drive', 'gateway of india']},
    'destination_goa':       {'weight': 10, 'keywords': ['goa', 'palolem', 'baga', 'anjuna', 'calangute']},
    'destination_jaipur':    {'weight': 10, 'keywords': ['jaipur', 'pink city', 'amber fort', 'hawa mahal']},
    'destination_bangalore': {'weight': 10, 'keywords': ['bangalore', 'bengaluru', 'garden city', 'lalbagh']},
    'destination_hyderabad': {'weight': 10, 'keywords': ['hyderabad', 'charminar', 'golconda', 'biryani city']},
    'destination_chennai':   {'weight': 10, 'keywords': ['chennai', 'madras', 'marina beach']},
    'destination_kolkata':   {'weight': 10, 'keywords': ['kolkata', 'calcutta', 'howrah', 'victoria memorial', 'city of joy']},
    'destination_varanasi':  {'weight': 10, 'keywords': ['varanasi', 'banaras', 'benares', 'kashi', 'ganga aarti']},
    'destination_udaipur':   {'weight': 10, 'keywords': ['udaipur', 'city of lakes', 'lake pichola']},
    'destination_agra':      {'weight': 10, 'keywords': ['agra', 'taj mahal', 'taj', 'fatehpur sikri']},
    'destination_kerala':    {'weight': 10, 'keywords': ['kerala', 'alleppey', 'munnar', 'kochi', 'cochin', 'backwaters', "god's own country"]},

    # --- Medium priority (weight 5): Specific topics ---
    'budget':    {'weight': 5, 'keywords': ['budget', 'cheap', 'save', 'money', 'afford', 'cost', 'price', 'discount', 'economical', 'frugal']},
    'booking':   {'weight': 5, 'keywords': ['book', 'cancel', 'pnr', 'payment', 'ticket', 'reservation', 'booking', 'refund']},
    'itinerary': {'weight': 5, 'keywords': ['plan', 'itinerary', 'schedule', 'route', 'travel plan', 'roadmap', 'days']},
    'weather':   {'weight': 5, 'keywords': ['weather', 'season', 'rain', 'monsoon', 'winter', 'summer', 'climate', 'when to visit', 'best time']},
    'food':      {'weight': 5, 'keywords': ['food', 'eat', 'restaurant', 'cuisine', 'dish', 'street food', 'snack', 'biryani', 'dosa', 'thali']},
    'safety':    {'weight': 5, 'keywords': ['safe', 'safety', 'danger', 'scam', 'precaution', 'emergency', 'police']},

    # --- Low priority (weight 1): Greetings & Thanks ---
    'greet':  {'weight': 1, 'keywords': ['hi', 'hello', 'hey', 'help', 'start', 'howdy', 'good morning', 'good evening', 'sup']},
    'thanks': {'weight': 1, 'keywords': ['thanks', 'thank you', 'thx', 'ty', 'appreciate', 'great', 'awesome', 'nice', 'cool']},
}


def _match_intent(message):
    """Match user message to the best intent using weighted scoring.

    Each keyword match adds the category's weight to its score.
    The category with the highest total score wins. If two categories
    tie, the one with more keyword matches wins. This ensures
    'destination_delhi' (weight 10) beats 'greet' (weight 1) even if
    'help' appears alongside 'delhi' in the message.
    """
    msg = message.lower().strip()
    scores = {}  # category -> (total_weight, match_count)

    for category, config in KEYWORDS.items():
        weight = config['weight']
        match_count = 0
        for kw in config['keywords']:
            if kw in msg:
                match_count += 1
        if match_count > 0:
            scores[category] = (weight * match_count, match_count)

    if not scores:
        return 'fallback'

    # Sort by total score (desc), then by match count (desc)
    best = max(scores.items(), key=lambda x: (x[1][0], x[1][1]))
    return best[0]


@chatbot_bp.route('', methods=['POST'])
def chat():
    """Handle chat messages and return rule-based responses."""
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'message is required'}), 400

    intent = _match_intent(message)
    reply = random.choice(RESPONSES[intent])

    return jsonify({
        'reply': reply,
        'intent': intent,
    })
