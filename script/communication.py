from flask import Blueprint, render_template, redirect, request, session, jsonify
from flask_socketio import SocketIO, send, emit
import sqlite3
import json

# Blueprint for communication functionalities
communication_bp = Blueprint('communication', __name__)

# Initialize SocketIO
socketio = SocketIO()

@socketio.on('send_message')
def handle_send_message(data):
    message = data['message']
    recipient = data['recipient']
    appointment_date = data['appointmentDate']
    appointment_time = data['appointmentTime']
    
    # Emit the message to the intended recipient
    socketio.emit('receive_message', {
        'message': message,
        'sender': session['username'],  # Use 'username' for session
        'appointmentDate': appointment_date,
        'appointmentTime': appointment_time
    }, room=recipient)

# Database connection utility
def get_db_connection():
    conn = sqlite3.connect('app_database.db')
    conn.row_factory = sqlite3.Row  # Allows dictionary-like row access
    return conn

# Messaging route example
@communication_bp.route('/messages')
def messages():
    recipient_username = request.args.get('recipient_username')  # Get the recipient from the URL
    if 'username' in session:  # Check 'username' in session
        return render_template('message.html', username=session['username'], recipient_username=recipient_username)
    else:
        return redirect('/')

# Schedule route example
@communication_bp.route('/schedule')
def schedule():
    if 'username' in session:
        conn = get_db_connection()
        user_schedule = conn.execute(
            'SELECT * FROM calendar WHERE username = ?',
            (session['username'],)
        ).fetchall()
        conn.close()
        return render_template('schedule.html', schedule=user_schedule)
    else:
        return redirect('/signup')

# Store calendar data in SQLite
@communication_bp.route('/storeCalendarData', methods=['POST'])
def store_calendar_data():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    jsdata = request.form['javascript_data']
    json_load_data = json.loads(jsdata)
    time = json_load_data['time']
    day = json_load_data['date']
    month = json_load_data['month']
    year = json_load_data['year']

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO calendar (username, time, day, month, year)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['username'], time, day, month, year))
    conn.commit()
    conn.close()

    return 'success'

# Video call route example
@communication_bp.route('/message/<recipient_username>')
def message(recipient_username):
    if 'username' not in session:
        return redirect('/login')

    # Check if recipient is a valid username (this part should be improved based on your DB structure)
    db = DatabaseConnection()
    recipient_user = db.get_user_by_username(recipient_username)  # Adjust based on your DB method
    
    if not recipient_user:
        return "Recipient not found", 404

    # Render the message page with the recipient's username
    return render_template('message.html', recipient_username=recipient_username)

# Video call route
@communication_bp.route('/video_call')
def video_call():
    if 'username' in session:
        return render_template('video_call.html', username=session['username'])
    else:
        return redirect('/')

@socketio.on('offer')
def handle_offer(offer):
    emit('offer', offer, broadcast=True)

@socketio.on('answer')
def handle_answer(answer):
    emit('answer', answer, broadcast=True)

@socketio.on('iceCandidate')
def handle_ice_candidate(candidate):
    emit('iceCandidate', candidate, broadcast=True)

# Registering socketio with the app later on
def register_socketio(app):
    socketio.init_app(app)
