import sqlite3

class DatabaseConnection:
    def __init__(self, db_name='app_database.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        # Create tables for doctors and patients
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

    def get_doctors(self):
        self.cursor.execute('SELECT id, name, phone, location, specialization FROM doctors WHERE confirmed = TRUE')
        doctors = self.cursor.fetchall()
        return [{'id': doc[0], 'name': doc[1], 'phone': doc[2], 'location': doc[3], 'specialization': doc[4]} for doc in doctors]

    def get_patients(self):
        self.cursor.execute('SELECT id, name, phone, username FROM patients')
        patients = self.cursor.fetchall()
        return [{'id': pat[0], 'name': pat[1], 'phone': pat[2], 'username': pat[3]} for pat in patients]

    def get_doctor_by_username(self, username):
        self.cursor.execute('SELECT * FROM doctors WHERE username = ?', (username,))
        doctor = self.cursor.fetchone()
        return doctor

    def get_patient_by_username(self, username):
        self.cursor.execute('SELECT * FROM patients WHERE username = ?', (username,))
        patient = self.cursor.fetchone()
        return patient
    
    def validate_user(self, username, password):
        # Check for doctor
        doctor = self.get_doctor_by_username(username)
        if doctor and doctor[6] == password:  # Assuming password is at index 6
            return 'doctor'  # Return user type

        # Check for patient
        patient = self.get_patient_by_username(username)
        if patient and patient[4] == password:  # Assuming password is at index 4
            return 'patient'  # Return user type

        return None  # Return None if credentials are invalid
    def update_doctor_info(self, current_username, name, phone, new_username, new_password, specialization):
    # SQL to update doctor information
        query = "UPDATE doctors SET username = %s, name = %s, phone = %s, password = %s, specialization = %s WHERE username = %s"
        values = (new_username, name, phone, new_password, specialization, current_username)
        self.execute_query(query, values)

    def update_patient_info(self, username, name, phone):
        """Update patient information in the database."""
        try:
            # Example SQL statement for updating patient information
            sql = """
            UPDATE patients
            SET name = %s, phone = %s
            WHERE username = %s
            """
            # Execute the query with parameters
            with self.connection.cursor() as cursor:
                cursor.execute(sql, (name, phone, username))
            self.connection.commit()  # Commit the changes
        except Exception as e:
            print(f"An error occurred: {e}")
            self.connection.rollback()
            
    def confirm_doctor(self, doctor_id):
        self.cursor.execute('''
            UPDATE doctors 
            SET confirmed = TRUE 
            WHERE id = ?
        ''', (doctor_id,))
        self.connection.commit()

    def close(self):
        self.connection.close()
