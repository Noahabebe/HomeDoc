from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import random
from flask_socketio import SocketIO, emit
from communication import communication_bp
from database import DatabaseConnection
import subprocess
import hashlib

id_mapping = {}

def hash_id(user_id):
    # Hash the user ID
    hashed = hashlib.sha256(str(user_id).encode()).hexdigest()
    
    # Store the mapping
    id_mapping[hashed] = user_id
    
    return hashed

def unhash_id(hashed_id):
    # Return the original user ID if the hashed ID exists in the mapping
    return id_mapping.get(hashed_id, None)

app = Flask(__name__)

app.register_blueprint(communication_bp, url_prefix='/communication')
socketio = SocketIO(app)


app.secret_key = "supersecretkey"

# DatabaseConnection class (to be defined with methods add_doctor, add_patient, get_patients, get_doctors)
from database import DatabaseConnection

# Function to search and download doctor info



def search_and_download_ahpra(doctor_name=None):
    with sync_playwright() as playwright:
        url = "https://www.ahpra.gov.au/Registration/Registers-of-Practitioners.aspx#search-results-anchor"
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(30000)
        page.goto(url)

        if doctor_name:
            # Fill the doctor name or registration number in the input field
            search_input = page.wait_for_selector("#name-reg", timeout=30000)
            search_input.fill(doctor_name)

            # Click on the search button
            search_button = page.wait_for_selector("#predictiveSearchHomeBtn", timeout=30000)
            search_button.click()

            # Wait for the search results to load
            page.wait_for_selector(".search-results-table", timeout=30000)

            # Extract practitioner details
            matching_doctors = []
            practitioner_elements = page.query_selector_all(".search-results-table")

            for practitioner in practitioner_elements:
                doctor_info= {}
                
                # Extract practitioner's full name
                name_tag = practitioner.query_selector(".search-results-table-col a")
                doctor_info['name'] = name_tag.inner_text().strip() if name_tag else "Name not available"
                
                # Extract practitioner's profession
                profession_tag = practitioner.query_selector(".search-results-table-col:nth-child(2) .text p")
                doctor_info['specialization'] = profession_tag.inner_text().strip() if profession_tag else "Profession not available"
                
                # Extract practitioner's location
                location_tag = practitioner.query_selector(".search-results-table-col:nth-child(4) .text p")
                doctor_info['location'] = location_tag.inner_text().strip() if location_tag else "Location not available"
                
                # Add the collected details to the list
                matching_doctors.append(doctor_info)
            
            print(matching_doctors)
            return matching_doctors

def search_and_download_hpcsa(doctor_name=None):
    # Example implementation for HPCSA (South Africa)
    # Add the scraping logic for HPCSA's website here
    pass

def search_and_download_ama(doctor_name=None, state=None):
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=True)  # Set headless=True for headless mode
        page = browser.new_page()
        page.set_default_timeout(30000)

        # Navigate to the AMA "Find a Doctor" page
        page.goto('https://find-doctor.ama-assn.org/')

        # Fill in the doctor's name (if provided)
        if doctor_name:
            page.fill('input#edit-name', doctor_name)

        # Fill in the location (if provided: city, city/state combination, or ZIP code)
        if state:
            page.fill('input#edit-location', state)
        else:
            print("state argument not passed!")

        # Click the "Search" button 
        page.click('input#edit-submit-api-search')

        # Wait for the search results to load (adjust the selector as needed based on the results section)
        page.wait_for_selector('.dr-finder-search-results-header')  # Wait until the results are displayed

        # Extract search results (adjust selectors based on the actual structure of the search results)
        results = page.query_selector_all('.dr-finder-search-result-card')  # Update this selector accordingly
        doctor_info = []

        for result in results:
            name = result.query_selector('.dr-finder-search-result-card__content__name').inner_text()  # Update as needed
            location = result.query_selector('.dr-finder-search-result-card__content__address').inner_text()
            specialties = result.query_selector('.dr-finder-search-result-card__content__specialty').inner_text()

            doctor_info.append({
                'name': name,
                'location': location,
                'specialization': specialties
            })
            print(doctor_info)

        # Close the browser
        browser.close()

        # Return the extracted doctor information
        return doctor_info


def search_and_download_cpso(doctor_name=None, cpso_number=None):
    
    with sync_playwright() as playwright:
        url = "https://doctors.cpso.on.ca/"
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(30000)
        page.goto(url)
        

        if cpso_number:
            
            search_input = page.wait_for_selector(".cpso-number", timeout=30000)
            search_input.fill(cpso_number)

            search_button = page.wait_for_selector("input[type='submit']", timeout=30000)
            search_button.click()

            
            page.wait_for_selector(".container-fluid.two_column_sticky_content_outer_container")
            
            matching_doctors = []
            # Extract doctor details
            doctor_info = {}

            # Get doctor name and CPSO number
            doctor_name_tag = page.query_selector("#docTitle")
            doctor_name_tag2 = doctor_name_tag.inner_text().strip() if doctor_name_tag else "Doctor name not available"


            
            # Get CPSO number
            cpso_number_tag = page.query_selector(".name_cpso_num h3")
            cpso_number_tag2 = cpso_number_tag.inner_text().split("#")[1].strip() if cpso_number_tag else "CPSO number not available"


            doctor_info['name'] = str(doctor_name_tag2 + ' (CPSO#' + cpso_number_tag2 + ')')
            
            
            # Get practice information
            practice_location_tag = page.query_selector("#practice_info .location_details")
            doctor_info['location'] = practice_location_tag.text_content().strip() if practice_location_tag else "Practice location not available"
            
            # Get phone and fax
            phone_tag = page.query_selector("#practice_info .location_details strong:has-text('Phone')")
            doctor_info['phone'] = phone_tag.text_content().strip() if phone_tag else "Phone not available"
            
            fax_tag = page.query_selector("#practice_info .location_details strong:has-text('Fax')")
            doctor_info['fax'] = fax_tag.text_content().strip() if fax_tag else "Fax not available"

            # Get specialization (if available)
            specialization_tag = page.query_selector("#specialties tbody tr td")
            doctor_info['specialization'] = specialization_tag.inner_text().strip() if specialization_tag else "Specialization not available"

            print(doctor_info)
            matching_doctors.append(doctor_info)
            return matching_doctors

        elif doctor_name:
            search_input = page.wait_for_selector(".cpso-lastname", timeout=30000)
            search_input.fill(doctor_name)

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
                print(matching_doctors)

            return matching_doctors

# Home route
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")

def get_current_user():
    # Assuming you are using session to store the logged-in user's username
    return session.get('username')

# Doctor search route
@app.route('/doctor_search', methods=['GET', 'POST'])
def doctor_search():
    if request.method == 'POST':
        doctor_name = request.form.get('doctor_name')
        cpso_number = request.form.get('cpso_number')
        state = request.form.get('state')
        region = request.form.get('region')

       

        # Process based on the selected region
        search_results = []
        if region == 'AMA':
            if not doctor_name:
               print("Doctor name is required!")
               return render_template('doctor_search.html', error="Doctor's last name is required!")
            if not state:
                print("State is required for AMA!")
                return render_template('doctor_search.html', error="State or ZIP code is required for AMA!")
            search_results = search_and_download_ama(doctor_name=doctor_name, state=state)
        elif region == 'AHPRA':
            search_results = search_and_download_ahpra(doctor_name=doctor_name)
        elif region == 'HPCSA':
            search_results = search_and_download_hpcsa(doctor_name)
        elif region == 'CPSO':
            search_results = search_and_download_cpso(doctor_name=doctor_name, cpso_number=cpso_number)
        else:
            return render_template('doctor_search.html', error="Please select a valid region!")

        # Render the results.html with the search results
        return render_template('results.html', doctors=search_results)

    return render_template('doctor_search.html')




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
    return redirect(url_for('doctor_login'))

# Sign up route for patients
@app.route("/patient_signup", methods=["GET", "POST"])
def patient_signup():
    if request.method == "POST":
        patient_name = request.form.get('patient_name')
        patient_phone = request.form.get('patient_phone')
        patient_username = request.form.get('patient_username')
        patient_password = request.form.get('patient_password')
        symptoms = request.form['symptoms']

        db = DatabaseConnection()
        db.add_patient(patient_name, patient_phone, patient_username, patient_password, symptoms)

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

@app.route("/dashboard")
def dashboard():
    if 'username' not in session:
        return redirect(url_for('doctor_login' if session.get('user_type') == 'doctor' else 'patient_login'))

    db = DatabaseConnection()
    user_type = session.get('user_type')
    username = session.get('username')



    if user_type == 'doctor':
        patients = db.get_patients()
        for patient in patients:
         patient['hashed_id'] = hash_id(patient['id'])
        return render_template('dashboard.html', patients=patients, user_type='doctor', username=username, id1=patient['hashed_id'])
    elif user_type == 'patient':
        doctors = db.get_doctors()
        for doctor in doctors:
         doctor['hashed_id'] = hash_id(doctor['id'])
        return render_template('dashboard.html', doctors=doctors, user_type='patient', username=username, id1=doctor['hashed_id'])
    return redirect(url_for('login'))

@app.route('/message/<recipient_id>', methods=['GET'])
def message(recipient_id):
    current_username = session.get('username')
    user_type = session.get('user_type')

    actual_recipient_id = unhash_id(recipient_id)
    # Fetch recipient's details from the database
    db = DatabaseConnection()
    recipient_details = db.get_contact_details(actual_recipient_id, user_type)
    
    # Check privacy settings
    if db.is_privacy_off_for_both(current_username, recipient_details['username']):
         recipient_display_name = recipient_details['name']
    else:

        recipient_display_name = recipient_id
       

    return render_template('message.html', 
                           recipient_username=recipient_display_name,
                           user_id=current_username)

@app.route('/send_message', methods=['POST'])
def send_message():
    sender_id = request.json.get('sender_id')

    recipient_id = request.json.get('recipient_id')
    message = request.json.get('message')
    user_type = session.get('user_type')
    db = DatabaseConnection()
    actual_sender_id = unhash_id(sender_id)
    actual_recipient_id = unhash_id(recipient_id)

    
    if not (db.is_privacy_off_for_both(actual_sender_id, actual_recipient_id)):

       
       
        sender_details = db.get_contact_details(actual_sender_id, user_type)
        recipient_details = db.get_contact_details(actual_recipient_id, user_type)

        hashed_sender_id = hash_id(sender_details['id'])
        hashed_recipient_id = hash_id(recipient_details['id'])

       
        emit('receive_message', {
            'sender': hashed_sender_id,
            'message': message
        }, room=hashed_recipient_id)

    else:
        # Privacy disabled, use real usernames
        sender_name = db.get_contact_details(actual_sender_id, user_type)['name']
        recipient_name = db.get_contact_details(actual_recipient_id, user_type)['name']

        # Emit the message with real usernames via Socket.IO
        emit('receive_message', {
            'sender': sender_name,
            'message': message
        }, room=recipient_name)

    return jsonify({'status': 'Message sent successfully'}), 200


@app.route('/match_doctors', methods=['POST'])
def match_doctors():
    db = DatabaseConnection()
    price_min = request.form.get('price_min')
    price_max = request.form.get('price_max')
    doctors = db.match_doctors_anonymous(price_min, price_max)
    return jsonify(doctors)


# Privacy Toggle Route
@app.route('/toggle_privacy', methods=['POST'])
def toggle_privacy():
    db = DatabaseConnection()
    username = session.get('username')
    user_type = session.get('user_type')
    if user_type == 'doctor':
        privacy_status = db.toggle_doctor_privacy(username)

    elif user_type == 'patient':
        privacy_status = db.toggle_patient_privacy(username)

    return jsonify({'status': 'success', 'privacy': privacy_status})


@app.route('/check_privacy_status', methods=['POST'])
def check_privacy_status():
    db = DatabaseConnection()
    data = request.json
    sender = data.get('sender')
    recipient = data.get('recipient')
    user_type = session.get('user_type')
    # Check if both parties have privacy off
    actual_recipient = unhash_id(recipient)
    if db.is_privacy_off_for_both(sender, actual_recipient):
        # Privacy is off, return contact details
        contact_details = db.get_contact_details(actual_recipient, user_type)
        return jsonify({'status': 'unlocked', 'details': contact_details})
    else:
        # Privacy still enabled, only messaging allowed
        return jsonify({'status': 'locked'})




# Video Call Route
@app.route('/start_video_call', methods=['POST'])
def start_video_call():
    db = DatabaseConnection()

    sender = request.json.get('sender')
    recipient = request.json.get('recipient')
    actual_sender= unhash_id(sender)
    actual_recipient = unhash_id(recipient)

    if db.is_privacy_off_for_both(actual_sender, actual_recipient):
        return jsonify({'status': 'success', 'message': 'You can start a video call.'})
    else:
        return jsonify({'status': 'error', 'message': 'Both parties must disable privacy for video call.'})


@app.route('/video_call/<recipient>')
def video_call(recipient):
    sender = session.get('username')
    recipient = unhash_id(recipient)
    return render_template('video_call.html', sender=sender, recipient=recipient)


# Settings Route
@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))

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
            db.update_doctor_info(current_username, name, phone, new_username, new_password, specialization)
        else:
            db.update_patient_info(current_username, name, phone, new_username, new_password)

        # Update session username if it has changed
        if new_username != current_username:
            session['username'] = new_username

        return redirect(url_for('dashboard'))

    return render_template("settings.html", user_info=user_info, user_type=user_type)


# Socket.IO events for messaging
@socketio.on('send_message')
def handle_message(data):
    sender = data['sender']
    recipient = data['recipient']
    message = data['message']
    user_type = session.get('user_type')
    db = DatabaseConnection()
    actual_sender= unhash_id(sender)
    actual_recipient = unhash_id(recipient)

    if not (db.is_privacy_off_for_both(actual_sender, actual_recipient)):
        # Privacy is enabled: Send anonymous message
        sender_id = db.get_contact_details(actual_sender, user_type)['id']
        hash_sender_id = hash_id(sender_id)

        emit('receive_message', {'sender': hash_sender_id, 'message': message}, room=recipient)
    else:
        # Privacy is disabled: Send real message
        sender_name = db.get_contact_details(actual_sender, user_type)['name']
        emit('receive_message', {'sender': sender_name, 'message': message}, room=recipient)






@socketio.on('offer')
def handle_offer(data):
    socketio.emit('offer', data, broadcast=True)


@socketio.on('answer')
def handle_answer(data):
    socketio.emit('answer', data, broadcast=True)


@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    socketio.emit('ice_candidate', data, broadcast=True)


# Logout Route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
