from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import random
from flask_socketio import SocketIO, emit
from communication import communication_bp
from database import DatabaseConnection
app = Flask(__name__)

app.register_blueprint(communication_bp, url_prefix='/communication')
socketio = SocketIO(app)


app.secret_key = "supersecretkey"

# DatabaseConnection class (to be defined with methods add_doctor, add_patient, get_patients, get_doctors)
from database import DatabaseConnection

# Function to search and download doctor info
def search_and_download(doctor_name=None, cpso_number=None):
    with sync_playwright() as playwright:
        url = "https://doctors.cpso.on.ca/"
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(30000)
        page.goto(url)

        if doctor_name:
            search_input = page.wait_for_selector(".cpso-lastname", timeout=30000)
            search_input.fill(doctor_name)
        elif cpso_number:
            number_input = page.wait_for_selector(".cpso-number", timeout=30000)
            number_input.fill(cpso_number)

        search_button = page.wait_for_selector("input[type='submit']", timeout=30000)
        search_button.click()

        page.wait_for_selector(".doctor-search-results--result", timeout=30000)
        page_html = page.content()
        soup = BeautifulSoup(page_html, 'html.parser')
        doctor_results = soup.find_all('article', class_='doctor-search-results--result')

        matching_doctors = []
        for result in doctor_results:
            doctor_info = {}
            doctor_name_tag = result.find('h3')
            doctor_info['name'] = doctor_name_tag.text.strip() if doctor_name_tag else "Name not available"
            address_section = result.find('p').text.strip()
            phone = fax = None
            location = ""
            address_lines = address_section.split("\n")
            for line in address_lines:
                if "Phone" in line:
                    phone = line.split("Phone:")[1].strip() if "Phone:" in line else None
                elif "Fax" in line:
                    fax = line.split("Fax:")[1].strip() if "Fax:" in line else None
                else:
                    location += f" {line}"
            doctor_info['location'] = location.strip() if location else "Location not available"
            doctor_info['phone'] = phone if phone else "Phone not available"
            doctor_info['fax'] = fax if fax else "Fax not available"
            specialization_tag = result.find('h4', text='Area(s) of Specialization:')
            specialization = specialization_tag.find_next('p').text.strip() if specialization_tag else "Specialization not available"
            doctor_info['specialization'] = specialization
            matching_doctors.append(doctor_info)

        return matching_doctors

# Home route
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

def get_current_user():
    # Assuming you are using session to store the logged-in user's username
    return session.get('username')

# Doctor search route
@app.route("/doctor_search", methods=["GET", "POST"])
def doctor_search():
    if request.method == "POST":
        doctor_name = request.form.get('doctor_name', '').strip()
        cpso_number = request.form.get('cpso_number', '').strip()

        if doctor_name:
            results = search_and_download(doctor_name=doctor_name)
        elif cpso_number:
            results = search_and_download(cpso_number=cpso_number)
        else:
            flash("Please enter either a doctor's name or a CPSO number.")
            return redirect(url_for('doctor_search'))

        if results:
            return render_template("results.html", doctors=results)
        else:
            flash("No matching doctors found.")
            return redirect(url_for('doctor_search'))

    return render_template("doctor_search.html")

# Edit signup route for doctors
@app.route("/edit_signup", methods=["GET", "POST"])
def edit_signup():
    doctor_name = request.args.get('doctor_name')
    doctor_phone = request.args.get('doctor_phone')
    doctor_location = request.args.get('doctor_location')
    doctor_specialization = request.args.get('doctor_specialization')
    doctor_username = request.args.get('doctor_username')  # Add username
    doctor_password = request.args.get('doctor_password')  # Add password

    if request.method == "POST":
        doctor_phone = request.form.get('doctor_phone')
        doctor_location = request.form.get('doctor_location')
        doctor_specialization = request.form.get('doctor_specialization')
        doctor_username = request.form.get('doctor_username')  # Collect username from form
        doctor_password = request.form.get('doctor_password')  # Collect password from form
        return redirect(url_for('finalize_signup', 
                                doctor_name=doctor_name,
                                doctor_phone=doctor_phone,
                                doctor_location=doctor_location,
                                doctor_specialization=doctor_specialization,
                                doctor_username=doctor_username,  # Pass username
                                doctor_password=doctor_password))  # Pass password

    return render_template(
        "edit_signup.html",
        doctor_name=doctor_name,
        doctor_phone=doctor_phone,
        doctor_location=doctor_location,
        doctor_specialization=doctor_specialization,
        doctor_username=doctor_username,  # Render username in form
        doctor_password=doctor_password   # Render password in form
    )

# Finalize doctor signup route
@app.route("/finalize_signup", methods=["GET", "POST"])
def finalize_signup():
    doctor_name = request.args.get('doctor_name')
    doctor_phone = request.args.get('doctor_phone')
    doctor_location = request.args.get('doctor_location')
    doctor_specialization = request.args.get('doctor_specialization')
    doctor_username = request.args.get('doctor_username')
    doctor_password = request.args.get('doctor_password')

    db = DatabaseConnection()
    db.add_doctor(doctor_name, doctor_phone, doctor_location, doctor_specialization, doctor_username, doctor_password)

    flash("Sign-up successful! Confirmation text sent.")
    return redirect(url_for('dashboard', user_type='doctor'))

# Sign up route for patients
@app.route("/patient_signup", methods=["GET", "POST"])
def patient_signup():
    if request.method == "POST":
        patient_name = request.form.get('patient_name')
        patient_phone = request.form.get('patient_phone')
        patient_username = request.form.get('patient_username')
        patient_password = request.form.get('patient_password')

        db = DatabaseConnection()
        db.add_patient(patient_name, patient_phone, patient_username, patient_password)

        flash("Sign-up successful!")
        return redirect(url_for('dashboard', user_type='patient'))

    return render_template("patient_signup.html") 

# Login route for doctors
@app.route("/doctor_login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        db = DatabaseConnection()
        doctor = db.get_doctor_by_username(username)

        if doctor and doctor[6] == password:  # Check password
            session['username'] = username  # Store username in session
            session['user_type'] = 'doctor'  # Store user type in session
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash("Invalid username or password.")
            return redirect(url_for('doctor_login'))  # Redirect back to login page

    return render_template("doctor_login.html")

# Patient Login Route
@app.route("/patient_login", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        db = DatabaseConnection()
        patient = db.get_patient_by_username(username)

        if patient and patient[4] == password:  # Check password
            session['username'] = username  # Store username in session
            session['user_type'] = 'patient'  # Store user type in session
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash("Invalid username or password.")
            return redirect(url_for('patient_login'))  # Redirect back to login page

    return render_template("patient_login.html")

# Dashboard route
@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('doctor_login' if session.get('user_type') == 'doctor' else 'patient_login'))

    db = DatabaseConnection()
    user_type = session.get('user_type')
    username = session.get('username')
    
    
    if user_type == 'doctor':
        user_info = db.get_doctor_by_username(username)
        patients = db.get_patients()
        return render_template("dashboard.html", user_type=user_type, user_info=user_info, patients=patients)

    elif user_type == 'patient':
        user_info = db.get_patient_by_username(username)
        doctors = db.get_doctors()
        return render_template("dashboard.html", user_type=user_type, user_info=user_info, doctors=doctors)

    return "Error: Invalid user type"

# Settings Route
@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    db = DatabaseConnection()
    current_username = session.get('username')
    user_type = session.get('user_type')

    # Fetch user information from the database
    if user_type == 'doctor':
        user_info = db.get_doctor_by_username(current_username)
    else:
        user_info = db.get_patient_by_username(current_username)

    # Handle form submission if the request is POST
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        new_username = request.form.get('username')
        new_password = request.form.get('password')

        # Update user info in the database
        if user_type == 'doctor':
            specialization = request.form.get('specialization')
            db.update_doctor_info(current_username, name, phone, new_username, new_password, specialization)  # Adjust based on your method
        else:
            db.update_patient_info(current_username, name, phone, new_username, new_password)  # Adjust based on your method

        # Update session username if it has changed
        if new_username != current_username:
            session['username'] = new_username

        return redirect(url_for('dashboard'))  # Redirect to dashboard after update

    return render_template("settings.html", user_info=user_info, user_type=user_type)

@app.route('/message/<recipient_username>')
def message(recipient_username):
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))

    # Check if recipient is a valid username
    db = DatabaseConnection()
    user_type = session.get('user_type')
    if user_type == 'doctor':
        recipient_user = db.get_doctor_by_username(recipient_username)
    else:
        recipient_user = db.get_patient_by_username(recipient_username)
    

    # Render the message page with the recipient's username
    return render_template('message.html', recipient_username=recipient_username)





@socketio.on('offer')
def handle_offer(data):
    # Handle the received offer
    socketio.emit('offer', data, broadcast=True)

@socketio.on('answer')
def handle_answer(data):
    # Handle the received answer
    socketio.emit('answer', data, broadcast=True)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    # Handle the received ICE candidate
    socketio.emit('ice_candidate', data, broadcast=True)

# Logout Route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('index'))  # Redirect to the home page

if __name__ == "__main__":
    socketio.run(app, debug=True)