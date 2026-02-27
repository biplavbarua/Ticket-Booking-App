"""Seed the database with 30 days of flights, trains, buses, hotels, and rooms + seat maps."""
import json, random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import Flight, Train, Bus, Hotel, Room, Seat

app = create_app()

# ── Route templates ────────────────────────────────────────────────
FLIGHT_ROUTES = [
    # (number, airline, origin, destination, dep_hour, dur_h, dur_m, price_base)
    ('AI-101', 'Air India', 'DEL', 'BOM', 6, 2, 15, 4500),
    ('6E-302', 'IndiGo', 'DEL', 'BOM', 9, 2, 10, 3800),
    ('UK-833', 'Vistara', 'BOM', 'DEL', 14, 2, 20, 5800),
    ('SG-155', 'SpiceJet', 'DEL', 'BLR', 7, 2, 30, 5200),
    ('6E-210', 'IndiGo', 'BLR', 'DEL', 15, 2, 45, 4200),
    ('AI-505', 'Air India', 'BOM', 'CCU', 11, 2, 30, 6100),
    ('AI-680', 'Air India', 'CCU', 'BOM', 10, 2, 45, 7200),
    ('SG-401', 'SpiceJet', 'DEL', 'CCU', 8, 2, 30, 4800),
    ('UK-621', 'Vistara', 'HYD', 'DEL', 12, 2, 20, 5500),
    ('6E-718', 'IndiGo', 'DEL', 'HYD', 16, 2, 30, 3900),
    ('SG-512', 'SpiceJet', 'BOM', 'BLR', 7, 1, 40, 3400),
    ('6E-450', 'IndiGo', 'BLR', 'BOM', 18, 1, 40, 3600),
    ('AI-330', 'Air India', 'DEL', 'GOI', 10, 2, 25, 5800),
    ('UK-410', 'Vistara', 'BLR', 'HYD', 6, 1, 10, 2900),
    ('6E-820', 'IndiGo', 'HYD', 'BLR', 20, 1, 10, 3100),
    ('SG-660', 'SpiceJet', 'CCU', 'DEL', 12, 2, 20, 4600),
    ('AI-210', 'Air India', 'BOM', 'GOI', 8, 1, 15, 3200),
    ('UK-990', 'Vistara', 'DEL', 'MAA', 14, 2, 50, 5400),
    ('6E-110', 'IndiGo', 'MAA', 'DEL', 6, 2, 50, 5000),
    ('SG-770', 'SpiceJet', 'BLR', 'CCU', 9, 2, 30, 5200),
]

TRAIN_ROUTES = [
    # (number, name, origin, destination, dep_h, dep_m, dur_h, classes_dict)
    ('12952', 'Mumbai Rajdhani', 'New Delhi', 'Mumbai Central', 16, 30, 16, {'SL': 450, '3A': 1250, '2A': 1850, '1A': 3100}),
    ('12951', 'Mumbai Rajdhani (Up)', 'Mumbai Central', 'New Delhi', 17, 0, 15, {'SL': 450, '3A': 1250, '2A': 1850, '1A': 3100}),
    ('12301', 'Howrah Rajdhani', 'New Delhi', 'Howrah', 17, 0, 17, {'3A': 1400, '2A': 2100, '1A': 3500}),
    ('12302', 'Howrah Rajdhani (Up)', 'Howrah', 'New Delhi', 14, 0, 17, {'3A': 1400, '2A': 2100, '1A': 3500}),
    ('12627', 'Karnataka Express', 'New Delhi', 'Bangalore', 21, 15, 33, {'SL': 580, '3A': 1500, '2A': 2200}),
    ('12259', 'Sealdah Duronto', 'New Delhi', 'Sealdah', 20, 20, 15, {'3A': 1350, '2A': 1950}),
    ('12723', 'Telangana Express', 'New Delhi', 'Hyderabad', 6, 50, 22, {'SL': 520, '3A': 1380, '2A': 2050}),
    ('12002', 'Bhopal Shatabdi', 'New Delhi', 'Bhopal', 6, 15, 8, {'CC': 980, 'EC': 1850}),
    ('12029', 'Swarna Shatabdi', 'New Delhi', 'Amritsar', 7, 20, 6, {'CC': 780, 'EC': 1450}),
    ('22691', 'Rajdhani Express', 'Bangalore', 'New Delhi', 20, 0, 34, {'3A': 1600, '2A': 2400, '1A': 3800}),
    ('12431', 'Trivandrum Rajdhani', 'New Delhi', 'Trivandrum', 10, 55, 42, {'3A': 1800, '2A': 2650, '1A': 4200}),
    ('12305', 'Kolkata Rajdhani', 'New Delhi', 'Howrah', 5, 0, 17, {'3A': 1500, '2A': 2200, '1A': 3700}),
    ('12622', 'Tamil Nadu Express', 'New Delhi', 'Chennai', 22, 30, 33, {'SL': 620, '3A': 1600, '2A': 2300}),
    ('12625', 'Kerala Express', 'New Delhi', 'Trivandrum', 11, 30, 46, {'SL': 700, '3A': 1900, '2A': 2800}),
    ('12565', 'Bihar S. Kranti Exp', 'New Delhi', 'Darbhanga', 14, 10, 19, {'SL': 400, '3A': 1050, '2A': 1550}),
    ('12011', 'Kalka Shatabdi', 'New Delhi', 'Chandigarh', 7, 40, 4, {'CC': 680, 'EC': 1250}),
    ('12012', 'Kalka Shatabdi (Up)', 'Chandigarh', 'New Delhi', 17, 10, 4, {'CC': 680, 'EC': 1250}),
]

BUS_ROUTES = [
    # (operator, origin, destination, dep_h, dur_h, bus_type, price)
    ('RedBus Travels', 'Delhi', 'Jaipur', 22, 6, 'Sleeper', 850),
    ('Raj National Express', 'Jaipur', 'Delhi', 23, 5, 'Sleeper', 900),
    ('VRL Travels', 'Bangalore', 'Goa', 21, 10, 'Semi-Sleeper', 1200),
    ('KSRTC', 'Bangalore', 'Chennai', 23, 6, 'Seater', 650),
    ('KPN Travels', 'Chennai', 'Bangalore', 22, 6, 'Semi-Sleeper', 750),
    ('MSRTC Shivneri', 'Mumbai', 'Pune', 7, 4, 'Seater', 450),
    ('MSRTC Shivneri', 'Pune', 'Mumbai', 7, 4, 'Seater', 450),
    ('Orange Travels', 'Hyderabad', 'Bangalore', 20, 10, 'Sleeper', 1100),
    ('SRS Travels', 'Delhi', 'Chandigarh', 6, 5, 'Seater', 550),
    ('Neeta Travels', 'Mumbai', 'Goa', 19, 12, 'Sleeper', 1350),
    ('TSRTC', 'Hyderabad', 'Chennai', 21, 9, 'Seater', 800),
    ('IntrCity SmartBus', 'Delhi', 'Agra', 6, 4, 'Seater', 350),
    ('IntrCity SmartBus', 'Agra', 'Delhi', 15, 4, 'Seater', 350),
    ('AbhiBus', 'Hyderabad', 'Vijayawada', 22, 5, 'Semi-Sleeper', 600),
    ('Kallada Travels', 'Bangalore', 'Trivandrum', 20, 12, 'Sleeper', 1400),
]

HOTELS_DATA = [
    ('The Grand Palace', 'Mumbai', 'Marine Drive, Colaba', 5, 'A luxurious 5-star hotel overlooking the Arabian Sea.',
     [('Standard', 5500, 15), ('Deluxe', 8500, 10), ('Suite', 15000, 4)]),
    ('Hotel Sunrise', 'Delhi', 'Connaught Place', 4, 'Premium business hotel in the heart of Delhi.',
     [('Standard', 3200, 20), ('Deluxe', 5800, 12), ('Suite', 9500, 5)]),
    ('Lakeview Resort', 'Bangalore', 'MG Road', 4, 'Modern hotel with a rooftop pool and city views.',
     [('Standard', 2800, 18), ('Deluxe', 4500, 10)]),
    ('Heritage Inn', 'Jaipur', 'MI Road, Pink City', 3, 'Charming heritage property with Rajasthani decor.',
     [('Standard', 1800, 22), ('Deluxe', 3200, 8), ('Suite', 5500, 3)]),
    ('Coastal Breeze', 'Goa', 'Calangute Beach Road', 4, 'Beachfront resort with infinity pool and spa.',
     [('Standard', 3500, 14), ('Deluxe Sea View', 6000, 8), ('Beach Villa', 12000, 3)]),
    ('Bay View Hotel', 'Chennai', 'Marina Beach Road', 4, 'Elegant waterfront hotel near the Marina.',
     [('Standard', 2600, 20), ('Deluxe', 4200, 12), ('Suite', 7500, 5)]),
    ('The Deccan Plaza', 'Hyderabad', 'Banjara Hills', 4, 'Contemporary luxury in the city of pearls.',
     [('Standard', 3000, 18), ('Deluxe', 5000, 10), ('Suite', 8000, 4)]),
    ('Kolkata Heritage', 'Kolkata', 'Park Street', 3, 'Classic charm blended with modern amenities.',
     [('Standard', 2200, 25), ('Deluxe', 3800, 12)]),
    ('The Ashoka', 'Delhi', 'Chanakyapuri', 5, 'Iconic 5-star hotel with lush gardens and heritage.',
     [('Standard', 6000, 12), ('Deluxe', 9000, 8), ('Presidential Suite', 22000, 2)]),
    ('Taj Lake Palace', 'Udaipur', 'Lake Pichola', 5, 'Floating palace on Lake Pichola — a once-in-a-lifetime stay.',
     [('Luxury Room', 18000, 8), ('Royal Suite', 35000, 3)]),
]


# ── Seat Generation Helpers ──────────────────────────────────────────

def generate_flight_seats(flight_id, num_seats):
    """Generate 3+3 layout seats (A-F across, 10 rows)."""
    seats = []
    cols = ['A', 'B', 'C', 'D', 'E', 'F']
    num_rows = max(num_seats // 6, 4)  # At least 4 rows
    total_generated = 0

    for row in range(1, num_rows + 1):
        for col_idx, col_letter in enumerate(cols):
            if total_generated >= num_seats:
                break
            seats.append(Seat(
                vehicle_type='flight',
                vehicle_id=flight_id,
                seat_label=f'{row}{col_letter}',
                row=row,
                col=col_idx,
                seat_class='economy',
                is_booked=random.random() < 0.25,  # 25% pre-booked
            ))
            total_generated += 1
    return seats


def generate_bus_seats(bus_id, num_seats):
    """Generate 2+2 layout seats (A-D across, ~10 rows)."""
    seats = []
    cols = ['A', 'B', 'C', 'D']
    num_rows = max(num_seats // 4, 5)
    total_generated = 0

    for row in range(1, num_rows + 1):
        for col_idx, col_letter in enumerate(cols):
            if total_generated >= num_seats:
                break
            seats.append(Seat(
                vehicle_type='bus',
                vehicle_id=bus_id,
                seat_label=f'{row}{col_letter}',
                row=row,
                col=col_idx,
                seat_class='standard',
                is_booked=random.random() < 0.3,  # 30% pre-booked
            ))
            total_generated += 1
    return seats


def generate_train_seats(train_id, num_seats):
    """Generate 8-berth compartment layout.
    Each compartment (row) has 8 berths:
      cols 0-2: Side A (LB, MB, UB)
      cols 3-5: Side B (LB, MB, UB)
      cols 6-7: Side berths (SL, SU)
    """
    seats = []
    berth_labels = ['LB', 'MB', 'UB', 'LB', 'MB', 'UB', 'SL', 'SU']
    num_compartments = max(num_seats // 8, 5)
    total_generated = 0

    for comp in range(1, num_compartments + 1):
        for col_idx, label in enumerate(berth_labels):
            if total_generated >= num_seats:
                break
            seats.append(Seat(
                vehicle_type='train',
                vehicle_id=train_id,
                seat_label=f'{label}-{comp}',
                row=comp,
                col=col_idx,
                seat_class='sleeper',
                is_booked=random.random() < 0.2,  # 20% pre-booked
            ))
            total_generated += 1
    return seats


def seed():
    with app.app_context():
        # Drop all existing data for a clean reseed
        print('🗑️  Clearing existing data...')
        Seat.query.delete()
        Room.query.delete()
        Hotel.query.delete()
        Bus.query.delete()
        Train.query.delete()
        Flight.query.delete()
        db.session.commit()

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_to_seed = 30
        flight_count = train_count = bus_count = seat_count = 0

        # ── Flights (every route, every day for 30 days) ──
        for day_offset in range(days_to_seed):
            base = today + timedelta(days=day_offset)
            for fn, airline, orig, dest, dep_h, dur_h, dur_m, price_base in FLIGHT_ROUTES:
                # Add small daily price variation (±10%)
                price = int(price_base * random.uniform(0.9, 1.1))
                seats = random.randint(20, 60)
                flight = Flight(
                    flight_number=fn, airline=airline, origin=orig, destination=dest,
                    departure=base + timedelta(hours=dep_h),
                    arrival=base + timedelta(hours=dep_h + dur_h, minutes=dur_m),
                    price=price, seats_available=seats,
                )
                db.session.add(flight)
                db.session.flush()

                # Generate seat map
                flight_seats = generate_flight_seats(flight.id, seats)
                db.session.add_all(flight_seats)
                seat_count += len(flight_seats)
                flight_count += 1

        # ── Trains (every route, every day for 30 days) ──
        for day_offset in range(days_to_seed):
            base = today + timedelta(days=day_offset)
            for tn, name, orig, dest, dep_h, dep_m, dur_h, classes in TRAIN_ROUTES:
                seats = random.randint(80, 200)
                train = Train(
                    train_number=tn, name=name, origin=orig, destination=dest,
                    departure=base + timedelta(hours=dep_h, minutes=dep_m),
                    arrival=base + timedelta(hours=dep_h + dur_h, minutes=dep_m),
                    classes=json.dumps(classes), seats_available=seats,
                )
                db.session.add(train)
                db.session.flush()

                train_seats = generate_train_seats(train.id, seats)
                db.session.add_all(train_seats)
                seat_count += len(train_seats)
                train_count += 1

        # ── Buses (every route, every day for 30 days) ──
        for day_offset in range(days_to_seed):
            base = today + timedelta(days=day_offset)
            for operator, orig, dest, dep_h, dur_h, bus_type, price_base in BUS_ROUTES:
                price = int(price_base * random.uniform(0.9, 1.1))
                seats = random.randint(20, 45)
                bus = Bus(
                    operator=operator, origin=orig, destination=dest,
                    departure=base + timedelta(hours=dep_h),
                    arrival=base + timedelta(hours=dep_h + dur_h),
                    bus_type=bus_type, price=price, seats_available=seats,
                )
                db.session.add(bus)
                db.session.flush()

                bus_seats = generate_bus_seats(bus.id, seats)
                db.session.add_all(bus_seats)
                seat_count += len(bus_seats)
                bus_count += 1

        # ── Hotels & Rooms (static, not date-dependent) ──
        hotel_count = 0
        for name, city, address, stars, desc, rooms_list in HOTELS_DATA:
            hotel = Hotel(name=name, city=city, address=address,
                          star_rating=stars, description=desc)
            db.session.add(hotel)
            db.session.flush()
            for room_type, ppn, avail in rooms_list:
                db.session.add(Room(
                    hotel_id=hotel.id, room_type=room_type,
                    price_per_night=ppn, rooms_available=avail,
                ))
            hotel_count += 1

        db.session.commit()
        print('✅ Database seeded successfully!')
        print(f'   → {flight_count} flights ({len(FLIGHT_ROUTES)} routes × {days_to_seed} days)')
        print(f'   → {train_count} trains ({len(TRAIN_ROUTES)} routes × {days_to_seed} days)')
        print(f'   → {bus_count} buses ({len(BUS_ROUTES)} routes × {days_to_seed} days)')
        print(f'   → {hotel_count} hotels with rooms')
        print(f'   → {seat_count} individual seat records')


if __name__ == '__main__':
    seed()
