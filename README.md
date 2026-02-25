<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-3.x-black?logo=flask" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-red?logo=databricks" />
  <img src="https://img.shields.io/badge/TailwindCSS-CDN-06B6D4?logo=tailwindcss&logoColor=white" />
</p>

<h1 align="center">🐍 Py-Booking</h1>
<h4 align="center">Your Journey, One Click Away</h4>
<p align="center">
  A full-stack travel booking platform built with Python & Flask.<br>
  <i>Flights, trains, buses & hotels — all in one place.</i>
</p>

---

> **📌 Academic Submission**
> This project is submitted in compliance with the **Final Project Submission** of the **PEP (Python for Everyone & Professionals) Class**, supervised by **Bhanu Teja Sir**.

---

## ✨ Features

| Module          | What it does                                                                  |
| --------------- | ----------------------------------------------------------------------------- |
| ✈️ **Flights**  | Search by city name (auto-resolves to IATA codes), browse results, book seats |
| 🚂 **Trains**   | Case-insensitive station search, class-wise pricing (SL/3A/2A/1A), PNR status |
| 🚌 **Buses**    | Filter by type (Sleeper/Semi-Sleeper/Seater), operator-wise results           |
| 🏨 **Hotels**   | City search, room type selection, date-based availability                     |
| 🔐 **Auth**     | Signup, Login, Logout with hashed passwords (PBKDF2-SHA256)                   |
| 👤 **Profile**  | View booking history, cancel bookings with confirmation modal                 |
| 💳 **Payments** | Mock payment gateway with booking confirmation & PNR generation               |

## 🏗️ Tech Stack

```
Backend  → Flask (Python micro-framework)
ORM      → SQLAlchemy + SQLite
Auth     → Flask-Login + Werkzeug password hashing
Frontend → Jinja2 templates + Tailwind CSS (CDN)
Fonts    → Google Fonts (Inter)
Icons    → Font Awesome 6
```

## 📁 Project Structure

```
Ticket-Booking-App/
├── app/
│   ├── blueprints/       # Route handlers (flights, trains, buses, hotels, auth)
│   ├── static/
│   │   ├── css/style.css # Custom stylesheet (dark theme)
│   │   └── js/app.js     # Client-side JS (tabs, autocomplete, loader)
│   ├── templates/        # Jinja2 HTML templates
│   ├── __init__.py       # App factory
│   ├── extensions.py     # Flask extensions
│   └── models.py         # SQLAlchemy models
├── config.py             # Configuration classes
├── seed_data.py          # Realistic data generator (30 days of schedules)
├── run.py                # Application entry point
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/biplavbarua/Ticket-Booking-App.git
cd Ticket-Booking-App

# 2. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed the database
python seed_data.py

# 5. Run the application
python run.py
```

Then open **http://127.0.0.1:5001** in your browser.

## 🗄️ Database Schema

```mermaid
erDiagram
    User ||--o{ Booking : makes
    Flight ||--o{ Booking : "booked as"
    Train ||--o{ Booking : "booked as"
    Bus ||--o{ Booking : "booked as"
    Hotel ||--o{ Room : has
    Room ||--o{ Booking : "booked as"

    User {
        int id PK
        string username
        string email
        string password_hash
    }

    Booking {
        int id PK
        string booking_type
        string pnr
        string status
        float total_price
        int user_id FK
    }
```

## 🎨 Design

The UI features a premium dark theme with a modern, professional aesthetic. Highlights include:

- **Tricolor stripe** & Ashoka Chakra–inspired logo for an Indian identity
- **Witty feature cards** — _"Faster than Tatkal"_, _"Fort Knox Security"_, _"Zero Downtime"_, _"No CAPTCHA Nightmares"_
- **Custom cancel modal** — a polished confirmation dialog for booking cancellations
- Built with **Tailwind CSS** (CDN) and **custom CSS variables**

## 📊 Seed Data

The `seed_data.py` script generates realistic travel data:

- **600 flights** across 20 Indian routes
- **510 trains** across 17 routes (including Rajdhani, Shatabdi, Express)
- **450 buses** across 15 routes
- **10 hotels** with multiple room types across 6 cities

## 🙏 Acknowledgements

- **Bhanu Teja Sir** — for supervising the PEP class and this project
- **Flask & SQLAlchemy** — for making Python web development a joy

---

<p align="center">
  No errors. Just bookings.<br>
  <sub>Built with ❤️ and questionable sleep schedules.</sub>
</p>
