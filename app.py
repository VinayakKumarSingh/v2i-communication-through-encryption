from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import json # For handling ABE attributes and ESP32 data
import os
from datetime import datetime

# Initialize Flask App
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_strong_secret_key_here') # Change in production!
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vehicle_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Redirect to login page if @login_required is used
login_manager.login_message_category = 'info' # Flash message category

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'doctor' or 'police'
    abe_attributes = db.Column(db.Text, nullable=True)  # JSON string for ABE attributes

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class VehicleData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(100), nullable=False, index=True)
    timestamp_server = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    payload = db.Column(db.Text, nullable=False) # Raw JSON payload from ESP32
    # For ABE, encrypted data might be stored here or in a related table
    # For simplicity, payload is stored as JSON text. Decryption would happen on access based on user.role and ABE attributes.

    def __repr__(self):
        return f'<VehicleData {self.id} for {self.vehicle_id} at {self.timestamp_server}>'

    @property
    def parsed_payload(self):
        try:
            return json.loads(self.payload)
        except json.JSONDecodeError:
            return {}

# Flask-Login User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch data based on role (placeholder for ABE logic)
    # For now, all data is fetched and filtered in template or here
    # In a real ABE system, decryption would occur here based on user's attributes
    
    # Fetch all data for now, sorted by most recent
    all_data = VehicleData.query.order_by(VehicleData.timestamp_server.desc()).limit(50).all()
    
    # Prepare data for template (convert payload string to dict)
    data_list_for_template = []
    for item in all_data:
        data_list_for_template.append({
            'id': item.id,
            'vehicle_id': item.vehicle_id,
            'timestamp_server': item.timestamp_server,
            'payload': item.parsed_payload # Use the property to get parsed JSON
        })

    return render_template('dashboard.html', title='Dashboard', data_list=data_list_for_template)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html', title='Login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        abe_attributes_str = request.form.get('abe_attributes')

        if not all([username, password, role]):
            flash('Username, password, and role are required.', 'warning')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))
        
        if role not in ['doctor', 'police']:
            flash('Invalid role selected.', 'danger')
            return redirect(url_for('register'))

        # Validate ABE attributes JSON (optional, basic check)
        abe_data = None
        if abe_attributes_str:
            try:
                abe_data = json.loads(abe_attributes_str)
                if not isinstance(abe_data, dict):
                    flash('ABE Attributes must be a valid JSON object (e.g., {"key": "value"}).', 'warning')
                    return redirect(url_for('register'))
            except json.JSONDecodeError:
                flash('Invalid JSON format for ABE Attributes.', 'warning')
                return redirect(url_for('register'))

        new_user = User(username=username, role=role, abe_attributes=json.dumps(abe_data) if abe_data else None)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- API Endpoints ---
@app.route('/api/vehicle_data', methods=['POST'])
def receive_vehicle_data():
    # This endpoint would ideally have some form of authentication (e.g., API key)
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    
    vehicle_id = data.get('vehicle_id')
    # The rest of the data is treated as payload
    # Example: data could be {'vehicle_id': 'ambulance01', 'latitude': 12.34, 'longitude': 56.78, 'temperature_c': 37.5, ...}

    if not vehicle_id:
        return jsonify({"error": "Missing vehicle_id"}), 400

    # Store the entire received JSON as payload, excluding vehicle_id if it's part of the main dict
    # Or, expect payload to be a nested dictionary.
    # For simplicity, let's assume the incoming data (excluding vehicle_id) is the payload.
    payload_data = {k: v for k, v in data.items() if k != 'vehicle_id'}

    if not payload_data:
        return jsonify({"error": "Missing payload data"}), 400

    try:
        new_data_entry = VehicleData(
            vehicle_id=vehicle_id,
            payload=json.dumps(payload_data) # Store the payload as a JSON string
        )
        db.session.add(new_data_entry)
        db.session.commit()
        return jsonify({"message": "Data received successfully", "id": new_data_entry.id}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving vehicle data: {e}")
        return jsonify({"error": "Failed to save data", "details": str(e)}), 500

# (Optional) API endpoint for AJAX map updates
@app.route('/api/latest_vehicle_data')
@login_required # Ensure only logged-in users can access this
def get_latest_vehicle_data():
    if current_user.role != 'police':
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch latest distinct location for each vehicle
    # This is a simplified query; a more robust solution might involve window functions or subqueries
    # depending on the database and exact requirements.
    latest_data = db.session.query(
        VehicleData.vehicle_id,
        db.func.max(VehicleData.timestamp_server).label('latest_timestamp'),
        VehicleData.payload
    ).group_by(VehicleData.vehicle_id).order_by(db.desc('latest_timestamp')).all()
    
    # This query above is not quite right for getting the payload of the latest. 
    # A better way for SQLite or simple cases:
    subquery = db.session.query(
        VehicleData.vehicle_id,
        db.func.max(VehicleData.id).label('max_id')
    ).group_by(VehicleData.vehicle_id).subquery()

    results = db.session.query(VehicleData).join(
        subquery, VehicleData.id == subquery.c.max_id
    ).all()

    locations = []
    for item in results:
        payload = item.parsed_payload
        if 'latitude' in payload and 'longitude' in payload:
            locations.append({
                'vehicle_id': item.vehicle_id,
                'payload': payload # Send the full parsed payload for map popups
            })
            
    return jsonify({"locations": locations})


# --- Utility / CLI Commands (Optional) ---
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    with app.app_context(): # Ensure we are in app context
        db.create_all()
    print('Initialized the database.')

@app.cli.command('create-admin')
def create_admin_command():
    """Creates a default admin/test user."""
    with app.app_context():
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
        role = input("Enter role (doctor/police): ").lower()
        if role not in ['doctor', 'police']:
            print("Invalid role. Must be 'doctor' or 'police'.")
            return
        
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists.")
            return

        admin_user = User(username=username, role=role)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"User {username} ({role}) created successfully.")

# --- Main Execution ---
if __name__ == '__main__':
    # Create tables if they don't exist (for development)
    # For production, use migrations (e.g., Flask-Migrate)
    with app.app_context():
        db.create_all() 
    app.run(debug=True, host='0.0.0.0', port=5000)