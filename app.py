import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from payu import payu

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_dev')

# Database helper function
def get_db_connection():
    conn = sqlite3.connect('consultancy.db')
    conn.row_factory = sqlite3.Row
    return conn

# User helper functions
def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def create_user(email, password, phone=None):
    conn = get_db_connection()
    hashed_password = generate_password_hash(password)
    try:
        conn.execute('''
            INSERT INTO users (email, password, phone)
            VALUES (?, ?, ?)
        ''', (email, hashed_password, phone))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def update_user_profile(user_id, email, phone=None):
    conn = get_db_connection()
    try:
        if phone:
            conn.execute('''
                UPDATE users
                SET email = ?, phone = ?
                WHERE id = ?
            ''', (email, phone, user_id))
        else:
            conn.execute('''
                UPDATE users
                SET email = ?
                WHERE id = ?
            ''', (email, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        return False

# Helper functions to fetch data from database
def get_services():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM services WHERE is_active = 1').fetchall()
    conn.close()
    return [dict(service) for service in services]

def get_service(service_id):
    conn = get_db_connection()
    service = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()
    conn.close()
    return dict(service) if service else None

def get_time_slots(service_id):
    conn = get_db_connection()
    slots = conn.execute('''
        SELECT * FROM time_slots 
        WHERE service_id = ? 
        ORDER BY date, start_time
    ''', (service_id,)).fetchall()
    conn.close()
    return [dict(slot) for slot in slots]

def get_user_bookings(user_id):
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, s.name as service_name, s.price, ts.date, ts.start_time, ts.end_time
        FROM bookings b
        JOIN services s ON b.service_id = s.id
        JOIN time_slots ts ON b.slot_id = ts.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def create_booking(user_id, service_id, slot_id):
    conn = get_db_connection()
    try:
        # Create booking
        cursor = conn.execute('''
            INSERT INTO bookings (user_id, service_id, slot_id, status)
            VALUES (?, ?, ?, 'PENDING')
        ''', (user_id, service_id, slot_id))
        
        booking_id = cursor.lastrowid
        
        # Get service price for payment
        service = conn.execute('SELECT price FROM services WHERE id = ?', (service_id,)).fetchone()
        
        # Create payment record
        conn.execute('''
            INSERT INTO payments (booking_id, amount, status)
            VALUES (?, ?, 'PENDING')
        ''', (booking_id, service['price']))
        
        # Mark slot as booked
        conn.execute('UPDATE time_slots SET is_booked = 1 WHERE id = ?', (slot_id,))
        
        conn.commit()
        conn.close()
        return booking_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return None

def update_booking_payment_status(booking_id, payment_status, booking_status=None):
    conn = get_db_connection()
    try:
        # Update payment status
        conn.execute('''
            UPDATE payments 
            SET status = ?, transaction_id = ?
            WHERE booking_id = ?
        ''', (payment_status, f"TXN{booking_id}", booking_id))
        
        # Update booking status if provided
        if booking_status:
            conn.execute('''
                UPDATE bookings 
                SET status = ?
                WHERE id = ?
            ''', (booking_status, booking_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/services')
def services():
    services = get_services()
    return render_template('services.html', services=services)

@app.route('/book/<int:service_id>')
def book_service(service_id):
    service = get_service(service_id)
    if not service:
        return redirect(url_for('services'))
    
    # Get time slots for this service
    slots = get_time_slots(service_id)
    return render_template('booking.html', service=service, slots=slots)

@app.route('/payment/success')
def payment_success():
    return render_template('payment_success.html')

@app.route('/payment/failed')
def payment_failed():
    return render_template('payment_failed.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/refund-policy')
def refund_policy():
    return render_template('refund_policy.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return redirect(url_for('account'))
        else:
            flash('Invalid email or password')
    
    return render_template('auth.html', active_tab='login')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('Email already registered')
            return render_template('auth.html', active_tab='signup')
        
        # Create new user
        user_id = create_user(email, password, phone)
        if user_id:
            flash('Account created successfully')
            return redirect(url_for('login'))
        else:
            flash('Error creating account')
            return render_template('auth.html', active_tab='signup')
    
    return render_template('auth.html', active_tab='signup')

@app.route('/account', methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    bookings = get_user_bookings(user_id)
    
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form.get('phone', '')
        
        if update_user_profile(user_id, email, phone):
            flash('Profile updated successfully')
            return redirect(url_for('account'))
        else:
            flash('Error updating profile')
    
    return render_template('account.html', user=user, bookings=bookings)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    return render_template('admin.html')

# API endpoints
@app.route('/api/create-order', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({
            "status": "error",
            "message": "Please login to create an order"
        }), 401
    
    user_id = session['user_id']
    service_id = request.form.get('service_id')
    slot_id = request.form.get('slot_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    if not service_id or not slot_id:
        return jsonify({
            "status": "error",
            "message": "Missing service or slot information"
        }), 400
    
    # Create booking
    booking_id = create_booking(user_id, service_id, slot_id)
    
    if booking_id:
        # Get service details for payment
        conn = get_db_connection()
        service = conn.execute('SELECT * FROM services WHERE id = ?', (service_id,)).fetchone()
        conn.close()
        
        # Create PayU payment request
        payment_data = payu.create_payment_request(
            booking_id=booking_id,
            amount=service['price'],
            productinfo=service['name'],
            firstname=first_name,
            email=email,
            phone=phone
        )
        
        # Return payment form HTML that will auto-submit to PayU
        payment_form = f'''
        <form id="payu-form" action="{payu.base_url}" method="post">
            <input type="hidden" name="key" value="{payment_data['key']}" />
            <input type="hidden" name="txnid" value="{payment_data['txnid']}" />
            <input type="hidden" name="amount" value="{payment_data['amount']}" />
            <input type="hidden" name="productinfo" value="{payment_data['productinfo']}" />
            <input type="hidden" name="firstname" value="{payment_data['firstname']}" />
            <input type="hidden" name="email" value="{payment_data['email']}" />
            <input type="hidden" name="phone" value="{payment_data['phone']}" />
            <input type="hidden" name="surl" value="{payment_data['surl']}" />
            <input type="hidden" name="furl" value="{payment_data['furl']}" />
            <input type="hidden" name="service_provider" value="{payment_data['service_provider']}" />
            <input type="hidden" name="hash" value="{payment_data['hash']}" />
        </form>
        <script>document.getElementById('payu-form').submit();</script>
        '''
        
        return jsonify({
            "status": "success",
            "message": "Redirecting to payment gateway",
            "payment_form": payment_form
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to create booking"
        }), 500

@app.route('/api/payu-callback', methods=['POST'])
def payu_callback():
    # Handle PayU callback
    response_data = request.form.to_dict()
    
    # Verify payment response
    if payu.verify_payment_response(response_data):
        # Update booking and payment status
        txnid = response_data.get('txnid', '')
        status = response_data.get('status', '')
        
        # Extract booking ID from transaction ID (format: TXN{booking_id}{amount})
        booking_id = None
        if txnid.startswith('TXN'):
            # Extract booking ID from transaction ID
            # This is a simplified approach - in production, you might want a more robust method
            try:
                # Assuming format TXN{booking_id}{amount}
                # We'll extract the booking ID by removing 'TXN' prefix and the amount suffix
                booking_id = int(''.join(filter(str.isdigit, txnid[3:])))
            except:
                pass
        
        if status.lower() == 'success' and booking_id:
            # Update payment status to SUCCESS
            # Update booking status to CONFIRMED
            update_booking_payment_status(booking_id, 'SUCCESS', 'CONFIRMED')
            # Send confirmation email (not implemented in this example)
            return jsonify({"status": "success", "message": "Payment verified successfully"})
        elif booking_id:
            # Update payment status to FAILED
            # Keep booking status as PENDING
            update_booking_payment_status(booking_id, 'FAILED')
            return jsonify({"status": "success", "message": "Payment failed"})
        else:
            return jsonify({"status": "error", "message": "Unable to process payment"}), 400
    else:
        return jsonify({"status": "error", "message": "Invalid payment response"}), 400

if __name__ == '__main__':
    print("Starting server on http://0.0.0.0:5000")
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
