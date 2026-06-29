from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import uuid
from datetime import datetime
from decimal import Decimal
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'eddies-bus-secret-key')

dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.environ.get('AWS_REGION', 'us-west-2'),
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)
bookings_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'EddieBusBookings'))

ROUTES = [
    {"id": "R001", "from": "Lagos",         "to": "Abuja",         "departure": "07:00 AM", "duration": "6 hrs", "price": 8500, "seats": 30},
    {"id": "R002", "from": "Lagos",         "to": "Port Harcourt", "departure": "09:00 AM", "duration": "5 hrs", "price": 7500, "seats": 30},
    {"id": "R003", "from": "Abuja",         "to": "Lagos",         "departure": "08:00 AM", "duration": "6 hrs", "price": 8500, "seats": 30},
    {"id": "R004", "from": "Abuja",         "to": "Kano",          "departure": "10:00 AM", "duration": "3 hrs", "price": 4500, "seats": 30},
    {"id": "R005", "from": "Port Harcourt", "to": "Lagos",         "departure": "06:00 AM", "duration": "5 hrs", "price": 7500, "seats": 30},
    {"id": "R006", "from": "Kano",          "to": "Abuja",         "departure": "11:00 AM", "duration": "3 hrs", "price": 4500, "seats": 30},
]

@app.route('/')
def index():
    return render_template('index.html', routes=ROUTES)

@app.route('/search', methods=['POST'])
def search():
    origin      = request.form.get('origin', '').strip()
    destination = request.form.get('destination', '').strip()
    travel_date = request.form.get('travel_date', '').strip()
    results = [
        r for r in ROUTES
        if r['from'].lower() == origin.lower()
        and r['to'].lower() == destination.lower()
    ]
    return render_template('search_results.html',
                           results=results,
                           origin=origin,
                           destination=destination,
                           travel_date=travel_date)

@app.route('/book/<route_id>', methods=['GET', 'POST'])
def book(route_id):
    route = next((r for r in ROUTES if r['id'] == route_id), None)
    if not route:
        flash('Route not found.', 'error')
        return redirect(url_for('index'))

    travel_date = request.args.get('travel_date', '')

    if request.method == 'POST':
        passenger_name  = request.form.get('passenger_name', '').strip()
        passenger_email = request.form.get('passenger_email', '').strip()
        passenger_phone = request.form.get('passenger_phone', '').strip()
        num_seats       = int(request.form.get('num_seats', 1))
        travel_date     = request.form.get('travel_date', '').strip()

        if not passenger_name or not passenger_email or not passenger_phone or not travel_date:
            flash('Please fill in all fields.', 'error')
            return render_template('book.html', route=route, travel_date=travel_date)

        ticket_id    = str(uuid.uuid4())[:8].upper()
        total_amount = route['price'] * num_seats

        try:
            bookings_table.put_item(Item={
                'ticket_id':       ticket_id,
                'route_id':        route_id,
                'passenger_name':  passenger_name,
                'passenger_email': passenger_email,
                'passenger_phone': passenger_phone,
                'num_seats':       num_seats,
                'travel_date':     travel_date,
                'origin':          route['from'],
                'destination':     route['to'],
                'departure_time':  route['departure'],
                'total_amount':    Decimal(str(total_amount)),
                'status':          'CONFIRMED',
                'booked_at':       datetime.utcnow().isoformat(),
            })
            return redirect(url_for('confirmation', ticket_id=ticket_id))
        except Exception as e:
            flash(f'Booking failed: {str(e)}', 'error')
            return render_template('book.html', route=route, travel_date=travel_date)

    return render_template('book.html', route=route, travel_date=travel_date)

@app.route('/confirmation/<ticket_id>')
def confirmation(ticket_id):
    try:
        response = bookings_table.get_item(Key={'ticket_id': ticket_id})
        booking  = response.get('Item')
        if not booking:
            flash('Booking not found.', 'error')
            return redirect(url_for('index'))
        return render_template('confirmation.html', booking=booking)
    except Exception as e:
        flash(f'Error retrieving booking: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/check-booking', methods=['GET', 'POST'])
def check_booking():
    booking = None
    if request.method == 'POST':
        ticket_id = request.form.get('ticket_id', '').strip().upper()
        try:
            response = bookings_table.get_item(Key={'ticket_id': ticket_id})
            booking  = response.get('Item')
            if not booking:
                flash('No booking found with that ticket ID.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('check_booking.html', booking=booking)

if __name__ == '__main__':
    app.run(debug=True)