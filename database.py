import sqlite3

class DatabaseConnection:
    def __init__(self, db_name='app_database.db'):
        # Establish connection to the SQLite database
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        # Create tables for doctors, patients, messages, and calendar
        self.cursor.execute('''        
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                location TEXT,
                specialization TEXT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                confirmed BOOLEAN DEFAULT FALSE
            )
        ''')

        self.cursor.execute('''        
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_username TEXT NOT NULL,
                receiver_username TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                time TEXT,
                day TEXT,
                month TEXT,
                year TEXT,
                FOREIGN KEY (username) REFERENCES patients (username)
            )
        ''')

        self.connection.commit()

    def add_doctor(self, name, phone, location, specialization, username, password):
        # Validate input
        if not name or not phone or not username or not password:
            raise ValueError("Doctor's name, phone, username, and password cannot be empty.")

        try:
            self.cursor.execute('''        
                INSERT INTO doctors (name, phone, location, specialization, username, password, confirmed) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, location, specialization, username, password, True))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting doctor: {e}")
            raise

    def add_patient(self, name, phone, username, password):
        # Validate input
        if not name or not phone or not username or not password:
            raise ValueError("Patient's name, phone, username, and password cannot be empty.")

        try:
            self.cursor.execute('''        
                INSERT INTO patients (name, phone, username, password) 
                VALUES (?, ?, ?, ?)
            ''', (name, phone, username, password))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting patient: {e}")
            raise

    def add_message(self, sender_username, receiver_username, message):
        # Validate input
        if not sender_username or not receiver_username or not message:
            raise ValueError("Sender, receiver, and message cannot be empty.")
        
        try:
            self.cursor.execute('''
                INSERT INTO messages (sender_username, receiver_username, message) 
                VALUES (?, ?, ?)
            ''', (sender_username, receiver_username, message))
            self.connection.commit()
        except Exception as e:
            print(f"Error inserting message: {e}")
            raise

    def get_messages(self, sender, receiver):
        # Fetch messages exchanged between two users
        self.cursor.execute('''
            SELECT sender_username, receiver_username, message, timestamp 
            FROM messages 
            WHERE (sender_username = ? AND receiver_username = ?) OR 
                  (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp
        ''', (sender, receiver, receiver, sender))
        messages = self.cursor.fetchall()
        return [{'sender': msg[0], 'receiver': msg[1], 'message': msg[2], 'timestamp': msg[3]} for msg in messages]

    def get_doctors(self):
        # Retrieve confirmed doctors
        self.cursor.execute('SELECT id, name, phone, location, specialization FROM doctors WHERE confirmed = 1')
        doctors = self.cursor.fetchall()
        return [{'id': doc[0], 'name': doc[1], 'phone': doc[2], 'location': doc[3], 'specialization': doc[4]} for doc in doctors]

    def get_patients(self):
        # Retrieve all patients
        self.cursor.execute('SELECT id, name, phone, username FROM patients')
        patients = self.cursor.fetchall()
        return [{'id': pat[0], 'name': pat[1], 'phone': pat[2], 'username': pat[3]} for pat in patients]

    def get_doctor_by_username(self, username):
        # Fetch doctor details by username
        self.cursor.execute('SELECT * FROM doctors WHERE username = ?', (username,))
        return self.cursor.fetchone()

    def get_patient_by_username(self, username):
        # Fetch patient details by username
        self.cursor.execute('SELECT * FROM patients WHERE username = ?', (username,))
        return self.cursor.fetchone()

    def validate_user(self, username, password):
        # Validate user credentials
        doctor = self.get_doctor_by_username(username)
        if doctor and doctor[6] == password:  # Assuming password is at index 6
            return 'doctor'

        patient = self.get_patient_by_username(username)
        if patient and patient[4] == password:  # Assuming password is at index 4
            return 'patient'

        return None

    def update_doctor_info(self, current_username, name, phone, new_username, new_password, specialization):
        # Update doctor information
        query = "UPDATE doctors SET username = ?, name = ?, phone = ?, password = ?, specialization = ? WHERE username = ?"
        values = (new_username, name, phone, new_password, specialization, current_username)
        self.cursor.execute(query, values)
        self.connection.commit()

    def update_patient_info(self, username, name, phone):
        # Update patient information
        try:
            sql = """
            UPDATE patients
            SET name = ?, phone = ?
            WHERE username = ?
            """
            self.cursor.execute(sql, (name, phone, username))
            self.connection.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.connection.rollback()

    def add_calendar_event(self, username, time, day, month, year):
        # Validate input
        if not username or not time or not day or not month or not year:
            raise ValueError("Username, time, day, month, and year cannot be empty.")
        
        try:
            self.cursor.execute('''
                INSERT INTO calendar (username, time, day, month, year) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, time, day, month, year))
            self.connection.commit()
        except Exception as e:
            print(f"Error adding calendar event: {e}")
            raise

    def get_calendar_events(self, username):
        # Fetch all calendar events for a specific user
        self.cursor.execute('''
            SELECT time, day, month, year 
            FROM calendar 
            WHERE username = ?
            ORDER BY year, month, day
        ''', (username,))
        events = self.cursor.fetchall()
        return [{'time': event[0], 'day': event[1], 'month': event[2], 'year': event[3]} for event in events]

    def get_messages_for_user(self, username):
        # Fetch all messages sent or received by a specific user
        self.cursor.execute(''' 
            SELECT sender_username, receiver_username, message, timestamp 
            FROM messages 
            WHERE sender_username = ? OR receiver_username = ? 
            ORDER BY timestamp
        ''', (username, username))
        messages = self.cursor.fetchall()
        return [{'sender': msg[0], 'receiver': msg[1], 'message': msg[2], 'timestamp': msg[3]} for msg in messages]

    def confirm_doctor(self, doctor_id):
        # Confirm a doctor's registration
        self.cursor.execute(''' 
            UPDATE doctors 
            SET confirmed = TRUE 
            WHERE id = ?
        ''', (doctor_id,))
        self.connection.commit()

    def close(self):
        # Close the database connection
        self.connection.close()
