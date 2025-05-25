# v2i-communication-through-encryption
# Smart Healthcare Emergency Vehicle Tracking and Monitoring System - Raspberry Pi Server

This directory contains the Flask web server application for the Smart Healthcare Emergency Vehicle Tracking and Monitoring System. It handles user authentication, data storage, role-based access control (potentially with Attribute-Based Encryption - ABE), and provides a web interface for authorized users (doctors, police) to view relevant data.

## Project Structure

```
raspberry_pi_server/
├── app.py                    # Main Flask application file
├── requirements.txt          # Python package dependencies
├── templates/                # HTML templates for the web interface
│   ├── base.html             # Base template for common layout
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # Dashboard for displaying data
│   └── ... (other templates)
├── static/                   # Static files (CSS, JavaScript, images) - (Create if needed)
│   └── css/
│       └── style.css         # Custom stylesheets (example)
│   └── js/
│       └── script.js         # Custom JavaScript (example)
├── instance/                 # Instance folder (auto-created by Flask for DB, etc.)
│   └── vehicle_data.db       # SQLite database file (created after init-db)
└── README.md                 # This file
```

## Setup and Installation

1.  **Clone the Repository (if applicable) or Navigate to Project Directory:**
    ```bash
    # If you cloned the entire project, navigate to this server directory
    cd raspberry_pi_server
    ```

2.  **Create a Python Virtual Environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    Install the required Python packages using pip and the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```
    *Note: If you plan to use a specific ABE library (e.g., `charm-crypto`), you might need to uncomment it in `requirements.txt` and follow its specific installation instructions, as some can have complex dependencies.*

4.  **Set Flask Environment Variables (Optional but Recommended):**
    For development, Flask runs in debug mode by default if `FLASK_ENV` is not set. You can explicitly set it.
    ```bash
    # For Windows (PowerShell)
    $env:FLASK_APP = "app.py"
    $env:FLASK_ENV = "development" # Enables debug mode
    # $env:FLASK_DEBUG = "1" # Alternative way to enable debug mode

    # For macOS/Linux (bash)
    export FLASK_APP=app.py
    export FLASK_ENV=development # Enables debug mode
    # export FLASK_DEBUG=1 # Alternative way to enable debug mode
    ```
    You might also want to set `SECRET_KEY` and `DATABASE_URL` as environment variables for better security and configuration management, especially for production.

5.  **Initialize the Database:**
    The application uses Flask-SQLAlchemy. Use the custom Flask CLI command to create the database tables.
    ```bash
    flask init-db
    ```
    This will create the `vehicle_data.db` file (or whatever is configured) in the `instance` folder (if not specified otherwise by `DATABASE_URL`).

6.  **Create an Admin/Test User (Optional but Recommended for Testing):**
    Use the custom Flask CLI command to create an initial user.
    ```bash
    flask create-admin
    ```
    You will be prompted to enter a username, password, and role (`doctor` or `police`).

## Running the Application

Once the setup is complete, you can run the Flask development server:

```bash
flask run
# Or, if you didn't set FLASK_APP environment variable:
# python app.py
```

The application will typically be available at `http://127.0.0.1:5000/` or `http://0.0.0.0:5000/` in your web browser.

## Key Features

*   **User Authentication:** Login, registration, and session management.
*   **Role-Based Access Control:** Different views and data access for 'doctor' and 'police' roles.
*   **Data Submission API:** Endpoint (`/api/vehicle_data`) for ESP32 or other devices to submit sensor data.
*   **Dashboard:** Displays relevant vehicle and medical data based on user role.
*   **Database:** SQLite for storing user and vehicle data.
*   **(Placeholder for) Attribute-Based Encryption (ABE):** The structure allows for future integration of ABE for fine-grained data encryption and access control over AES keys used to encrypt the actual data.

## ESP32 Data Submission

The ESP32 devices should send data as a JSON payload to the `/api/vehicle_data` endpoint via a POST request.

**Example JSON Payload:**
```json
{
    "vehicle_id": "ambulance_01",
    "timestamp_device": "2023-10-27T10:30:00Z", // ISO 8601 format recommended
    "latitude": 34.0522,
    "longitude": -118.2437,
    "speed_kmh": 60.5,
    "temperature_c": 37.2,       // Medical data
    "humidity_percent": 45.0,    // Medical data
    "heart_rate_bpm": 88,        // Medical data
    "blood_oxygen_spo2": 98.5,   // Medical data
    "patient_name": "John Doe",    // Optional patient identifier
    "medical_id": "MED00123"     // Optional medical record ID
}
```

*   The `vehicle_id` is mandatory.
*   Other fields are part of the payload that gets stored.
*   The server will then (in a full ABE implementation) encrypt this payload with an AES key, and then encrypt the AES key using ABE policies for different roles before storing.

## Further Development & ABE Integration

*   **ABE Library:** Choose and integrate an ABE library (e.g., `charm-crypto`, `pyabe`). This will involve:
    *   Setting up ABE master keys and public parameters.
    *   Modifying the `User` model to store ABE private keys (or a way to derive them).
    *   Updating the data submission and retrieval logic in `app.py` to perform actual ABE encryption/decryption of AES keys.
    *   Defining clear ABE policies for data access.
*   **Static Files:** Create a `static` directory for CSS, JavaScript, and images if you need custom styling or client-side interactions beyond what Bootstrap provides in `base.html`.
*   **Error Handling:** Enhance error handling and logging.
*   **Security:** Implement CSRF protection, review security headers, and ensure robust input validation.
*   **Testing:** Write unit and integration tests.
*   **Deployment:** For production, use a proper WSGI server (like Gunicorn or Waitress) and consider containerization (e.g., Docker).
