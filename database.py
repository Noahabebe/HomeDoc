import sqlite3

class DatabaseConnection:
    def __init__(self, db_name='app_database.db'):
        # Establish connection to the SQLite database
        self.connection = sqlite3.connect(db_name)
        self.connection.row_factory = sqlite3.Row  # Set row factory to return rows as dictionaries
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
                confirmed BOOLEAN DEFAULT FALSE,
                privacy BOOLEAN DEFAULT TRUE
            )

        ''')

        self.cursor.execute('''        
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                symptoms TEXT,
                privacy BOOLEAN DEFAULT TRUE
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
       

        try:
            self.cursor.execute('''        
                INSERT INTO doctors (name, phone, location, specialization, username, password, confirmed) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, location, specialization, username, password, True))
            self.connection.commit()
        except sqlite3.IntegrityError as e:
            print(f"Error inserting doctor: {e}")
            raise

    def add_patient(self, name, phone, username, password, symptoms):
    # Validate input
       

        try:
            self.cursor.execute('''        
                INSERT INTO patients (name, phone, username, password, symptoms) 
                VALUES (?, ?, ?, ?, ?)
            ''', (name, phone, username, password, symptoms))  # Add symptoms here
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
        query = "SELECT id, username, name, specialization, location, phone FROM doctors"
        return self._execute_query(query)

    def get_patients(self):
        query = "SELECT id, username, name, phone, symptoms FROM patients"
        return self._execute_query(query)

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
        query = ''' 
            UPDATE doctors 
            SET username = ?, name = ?, phone = ?, password = ?, specialization = ? 
            WHERE username = ?
        '''
        values = (new_username, name, phone, new_password, specialization, current_username)
        self.cursor.execute(query, values)
        self.connection.commit()

    def update_patient_info(self, username, name, phone):
        # Update patient information
        try:
            sql = ''' 
            UPDATE patients 
            SET name = ?, phone = ? 
            WHERE username = ? 
            '''
            self.cursor.execute(sql, (name, phone, username))
            self.connection.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.connection.rollback()

    def get_contact_details(self, identifier, user_type):
        if user_type == 'doctor':
            # Query for doctors
            query_username = '''SELECT id, username, name FROM doctors WHERE username = ?'''
            query_id = '''SELECT id, username, name FROM doctors WHERE id = ?'''
            
            # First, check if the identifier matches a username
            result = self.cursor.execute(query_username, (identifier,))
            user_details = result.fetchone()  # Use fetchone to get a single row
            
            if user_details:
                return {
                    'id': user_details['id'],        # Access by column name
                    'username': user_details['username'],   # Access by column name
                    'name': user_details['name']        # Access by column name
                }

            # Check if the identifier matches an ID
            result = self.cursor.execute(query_id, (identifier,))
            user_details = result.fetchone()
            
            if user_details:
                return {
                    'id': user_details['id'],         # Access by column name
                    'username': user_details['username'],    # Access by column name
                    'name': user_details['name']         # Access by column name
                }

        else:  # Assuming user_type is 'patient'
            # Query for patients
            query_username = '''SELECT id, username, name FROM patients WHERE username = ?'''
            query_id = '''SELECT id, username, name FROM patients WHERE id = ?'''

            # First, check if the identifier matches a username
            result = self.cursor.execute(query_username, (identifier,))
            user_details = result.fetchone()  # Use fetchone to get a single row
            
            if user_details:
                return {
                    'id': user_details['id'],        # Access by column name
                    'username': user_details['username'],   # Access by column name
                    'name': user_details['name']        # Access by column name
                }

            # Check if the identifier matches an ID
            result = self.cursor.execute(query_id, (identifier,))
            user_details = result.fetchone()
            
            if user_details:
                return {
                    'id': user_details['id'],         # Access by column name
                    'username': user_details['username'],    # Access by column name
                    'name': user_details['name']         # Access by column name
                }

        return None
    
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

    def get_patients_anonymous(self):
        query = "SELECT 'Anonymous' AS name, symptoms FROM patients WHERE privacy = 1"
        return self._execute_query(query)

    # Fetch doctors anonymously (showing only specialization)
    def get_doctors_anonymous(self):
        query = "SELECT 'Anonymous' AS name, specialization FROM doctors WHERE privacy = 1"
        return self._execute_query(query)

    # Match doctors based on price range and anonymity
    def match_doctors_anonymous(self, price_min, price_max):
        query = '''
            SELECT 'Anonymous' AS name, specialization 
            FROM doctors 
            WHERE price >= ? AND price <= ? AND privacy = 1
        '''
        return self._execute_query(query, (price_min, price_max))

    # Toggle doctor privacy
    def toggle_doctor_privacy(self, doctor_username):
        query = "UPDATE doctors SET privacy = NOT privacy WHERE username = ? RETURNING privacy"
        result = self._execute_query(query, (doctor_username,))
        return result[0]['privacy']

    # Toggle patient privacy
    def toggle_patient_privacy(self, patient_username):
        query = "UPDATE patients SET privacy = NOT privacy WHERE username = ? RETURNING privacy"
        result = self._execute_query(query, (patient_username,))
        return result[0]['privacy']

    # Check if privacy is off for both parties
    def is_privacy_off_for_both(self, sender_username, recipient_username):
        # Check sender and recipient privacy
        sender_privacy = self.get_privacy_status(sender_username)
        recipient_privacy = self.get_privacy_status(recipient_username)

        return sender_privacy  and recipient_privacy  # Both must have privacy off

    # Get privacy status of a user
    def get_privacy_status(self, username):
        self.cursor.execute('SELECT privacy FROM doctors WHERE username = ? UNION SELECT privacy FROM patients WHERE username = ?', (username, username))
        return self.cursor.fetchone()

    # Helper method to execute queries
    def _execute_query(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return [dict(zip([column[0] for column in self.cursor.description], row)) for row in self.cursor.fetchall()]

    def close(self):
        # Close the database connection
        self.connection.close()

if __name__ == "__main__":
    db = DatabaseConnection()
