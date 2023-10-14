import hashlib
import os
import random
from functools import wraps
from io import BytesIO
import face_recognition
import json
from mysql.connector import Error
import subprocess


import cv2
import mysql.connector
import qrcode
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "gate"

# Define the path to the dataset folder where your images are located
dataset_path = "dataset"
encodings_folder = "encodings"

# Configure your MySQL database connection
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Fill in your MySQL password here
    'database': 'gate',
}

# Function to count failed authentication attempts
def get_failed_auth_count():
    try:
        # Create a database connection and cursor
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Query the database to count failed authentication attempts
        query = "SELECT COUNT(*) FROM auth_log WHERE actions = 'Authentication Failed'"
        cursor.execute(query)
        failed_auth_count = cursor.fetchone()[0]

        return failed_auth_count
    except mysql.connector.Error as err:
        # Handle any database errors here
        print(f"Error: {err}")
    finally:
        # Close the cursor and connection in the 'finally' block to ensure it always happens
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Function to count successful authentication attempts
def get_successful_auth_count():
    try:
        # Create a database connection and cursor
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Query the database to count successful authentication attempts
        query = "SELECT COUNT(*) FROM auth_log WHERE actions = 'Authentication Successful'"
        cursor.execute(query)
        successful_auth_count = cursor.fetchone()[0]

        return successful_auth_count
    except mysql.connector.Error as err:
        # Handle any database errors here
        print(f"Error: {err}")
    finally:
        # Close the cursor and connection in the 'finally' block to ensure it always happens
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def get_user_name_by_id(user_id):
    try:
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            cursor = connection.cursor()
            # Prepare the SELECT statement to fetch user's name based on user_id
            select_query = "SELECT firstname, lastname FROM reg_user WHERE user_id = %s"
            cursor.execute(select_query, (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                first_name, last_name = user_data
                full_name = f"{first_name} {last_name}"
                return full_name
            else:
                return "Unknown User"  # Return a default value if user not found
    except Error as e:
        print(f"[ERROR] Error fetching user name: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def log_authentication_success(user_id, action):
    try:
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            cursor = connection.cursor()
            # Prepare the INSERT statement
            insert_query = "INSERT INTO auth_log (name, actions) VALUES (%s, %s)"
            # Get the user's name from the database based on user_id (you need to implement this)
            user_name = get_user_name_by_id(user_id)
            # Execute the INSERT statement
            cursor.execute(insert_query, (user_name, action))
            connection.commit()
            print("[INFO] Authentication logged successfully")
    except Error as e:
        print(f"[ERROR] Error logging authentication: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def log_authentication_failed(user_id, action):
    try:
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            cursor = connection.cursor()
            # Prepare the INSERT statement
            insert_query = "INSERT INTO auth_log (name, actions) VALUES (%s, %s)"
            # Get the user's name from the database based on user_id (you need to implement this)
            user_name = get_user_name_by_id(user_id)
            # Execute the INSERT statement
            cursor.execute(insert_query, (user_name, action))
            connection.commit()
            print("[INFO] Authentication logged successfully")
    except Error as e:
        print(f"[ERROR] Error logging authentication: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_db_connection():
    return mysql.connector.connect(**db_config)

# Function to fetch the number of logs in auth_log table
def get_logs_count():
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM auth_log")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print("Error:", e)
        return 0  # Return 0 if there's an error

# Function to fetch the number of registered users
def get_registered_users_count():
    conn = create_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM reg_user")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

# Function to authenticate the user
def authenticate(username, password):
    try:
        conn = create_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        print("Error:", e)
        return None

def load_encodings_from_database():
    encodings = {}
    try:
        # Establish a connection to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Retrieve encodings from the database
        cursor.execute("SELECT user_id, encoding FROM encodings")
        rows = cursor.fetchall()

        for row in rows:
            user_id, encoding_data = row
            encoding_list = json.loads(encoding_data)
            encodings[user_id] = encoding_list

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error loading encodings from the database: {str(e)}")

    return encodings

def authenticate_with_qrcode(user_id):
    try:
        # Create a database connection
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Retrieve hashed PIN from the 'face_image' table
        cursor.execute("SELECT hashed_pin FROM face_image WHERE user_id = %s", (user_id,))
        hashed_pin = cursor.fetchone()

        cursor.close()
        db.close()

        if hashed_pin:
            return hashed_pin[0]

    except Exception as e:
        print(f"Error fetching hashed PIN from the database: {str(e)}")

    return None

# Function to fetch data from the MySQL database
def get_user_data():
    conn = create_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, firstname, lastname, phone_number, gender, reg_date FROM reg_user")
    user_data = cursor.fetchall()
    conn.close()
    return user_data

# Define the custom login_required decorator
def login_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        # Check if the user is authenticated (e.g., by checking the session)
        if 'user' in session:
            return view_func(*args, **kwargs)
        else:
            # User is not authenticated, redirect to the login page
            return redirect(url_for('login'))
    return decorated_view

# Route for the login page
@app.route('/', methods=['GET', 'POST'])
def login():
    error_message = None  # Initialize error_message as None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)

        if user:
            # Authentication successful, redirect to dashboard.html
            session['user'] = username  # Store user session
            return redirect(url_for('dashboard'))
        else:
            # Authentication failed, set the error_message
            error_message = "Wrong Username or Password"

    return render_template('login.html', error_message=error_message)

# Route for the dashboard page
# Route for the dashboard page
@app.route('/dashboard')
@login_required
def dashboard():
    # Get the number of registered users
    user_count = get_registered_users_count()

    # Get the number of logs
    log_count = get_logs_count()

    # Get the count of successful authentication attempts using the new function
    successful_auth_count = get_successful_auth_count()

    # Get the count of failed authentication attempts
    failed_auth_count = get_failed_auth_count()

    # Get the username from the session
    username = session.get('user')

    return render_template('dashboard.html', user_count=user_count, successful_auth_count=successful_auth_count, failed_auth_count=failed_auth_count, log_count=log_count, username=username)

@app.route('/user_management')
@login_required
def user_management():
    user_data = get_user_data()
    return render_template('usrmgmt.html', user_data=user_data)

# Route for deleting a user
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM reg_user WHERE user_id = %s", (user_id,))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
        print(e)
    finally:
        conn.close()

    return jsonify({"success": success})

# Route for editing a user
@app.route('/edit_user/<int:user_id>', methods=['GET'])
@login_required
def edit_user(user_id):
    conn = create_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, firstname, lastname, phone_number, gender FROM reg_user WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data:
        return render_template('edit.html', user=user_data)
    else:
        return "User not found", 404

# Route for updating a user
@app.route('/update_user', methods=['POST'])
@login_required
def update_user():
    user_id = request.form.get('user_id')  # Retrieve user_id from the form data
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    gender = request.form.get('gender')
    phone_number = request.form.get('phone_number')

    conn = create_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE reg_user SET firstname=%s, lastname=%s, gender=%s, phone_number=%s WHERE user_id=%s", (firstname, lastname, gender, phone_number, user_id))
        conn.commit()
        success = True
    except Exception as e:
        conn.rollback()
        success = False
        print(e)
    finally:
        conn.close()

    if success:
        return redirect(url_for('user_management'))
    else:
        return "Failed to update user", 500

# Route for the user registration form
@app.route('/add_user')
def add_user():
    return render_template('form.html')

# Define your route for submitting the user registration form
@app.route('/submit_form', methods=['POST'])
def submit_form():
    global frame
    try:
        # Extract form data from the request
        firstname = request.form["first_name"]
        lastname = request.form["last_name"]
        phone_number = request.form["phone_number"]
        gender = request.form["gender"]

        # Generate a random three-digit number for the ID
        user_id = f"{random.randint(1000, 9999)}"

        # Generate a random PIN
        pin = random.randint(1000, 9999)

        # Hash the PIN using SHA-256
        hashed_pin = hashlib.sha256(str(pin).encode()).hexdigest()

        # Generate a QR code for the user_id and hashed_pin
        qr_data = f"user_id: {user_id}\nhashed_pin: {hashed_pin}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save the QR code image to BytesIO object
        qr_img_bytesio = BytesIO()
        qr_img.save(qr_img_bytesio, format="PNG")
        qr_img_bytes = qr_img_bytesio.getvalue()

        # Define the path to the dataset folder
        dataset_folder = "dataset"
        name_folder = os.path.join(dataset_folder, user_id)

        # Create the dataset folder if it doesn't exist
        if not os.path.exists(name_folder):
            os.makedirs(name_folder)

        # Save the QR code image to a file on the server
        qr_code_file_path = os.path.join(name_folder, "qr_code.png")
        qr_img.save(qr_code_file_path, format="PNG")

        # Define the path for the PIN file
        pin_file_path = os.path.join(name_folder, "pin.txt")

        # Save the hashed PIN to a text file
        with open(pin_file_path, "w") as pin_file:
            pin_file.write(hashed_pin)

        # Create a database connection
        db = create_db_connection()
        cursor = db.cursor()

        try:
            # Insert user data into the 'reg_user' table, including the registration date
            insert_user_query = "INSERT INTO reg_user (user_id, firstname, lastname, phone_number, gender, reg_date) VALUES (%s, %s, %s, %s, %s, NOW())"
            user_data = (user_id, firstname, lastname, phone_number, gender)
            cursor.execute(insert_user_query, user_data)
            db.commit()

            # Initialize the camera
            cam = cv2.VideoCapture(0)

            # Create a resizable window
            cv2.namedWindow("Press space to take a photo", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Press space to take a photo", 500, 400)

            img_counter = 0
            max_images = 10  # Limit the number of images to 10

            while img_counter < max_images:
                ret, frame = cam.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                cv2.imshow("Press space to take a photo", frame)

                k = cv2.waitKey(1)
                if k % 256 == 27:
                    # ESC pressed
                    print("Escape hit, closing...")
                    break
                elif k % 256 == 32:
                    # SPACE pressed
                    img_name = f"{name_folder}/image_{img_counter}.jpg"
                    cv2.imwrite(img_name, frame)
                    print(f"{img_name} written!")

                    img_counter += 1

            # Release the camera and close the OpenCV window
            cam.release()
            cv2.destroyAllWindows()

            # Insert user data, hashed_pin, and QR code image into the 'face_image' table
            insert_face_image_query = "INSERT INTO face_image (user_id, img_data, qr_code, hashed_pin) VALUES (%s, %s, %s, %s)"
            face_image_data = (user_id, cv2.imencode('.jpg', frame)[1].tobytes(), qr_img_bytes, hashed_pin)
            cursor.execute(insert_face_image_query, face_image_data)
            db.commit()

            success_message = f"User data saved to the database, {img_counter} images saved to {name_folder}, and hashed PIN saved to {pin_file_path}"

            return redirect(url_for('user_management'))

        except mysql.connector.Error as err:
            error_message = f"Error: {err}"
            return jsonify({"error_message": error_message})

        finally:
            cursor.close()
            db.close()

    except Exception as e:
        error_message = f"Error: {str(e)}"
        return jsonify({"error_message": error_message})

# Define a route to render the HTML template
@app.route('/logs')
def logs():
    try:
        # Establish a database connection
        db = mysql.connector.connect(**db_config)

        # Fetch data from the auth_log table
        cursor = db.cursor()
        cursor.execute("""
            SELECT auth_log.auth_id, auth_log.name, auth_log.actions, auth_log.time_stamp
            FROM auth_log
            ORDER BY auth_log.time_stamp DESC  # Order logs by timestamp in descending order
        """)
        log_data = cursor.fetchall()

        # Close the database connection
        db.close()

        # Render the HTML template and pass the data to it
        return render_template('logs.html', log_data=log_data)
    except mysql.connector.Error as e:
        # Handle any database connection errors here
        return "Error connecting to the database: " + str(e)

@app.route('/train_model', methods=['POST'])
def train_model():
    try:
        print("[INFO] Start processing faces...")

        # Create the encodings folder if it doesn't exist
        if not os.path.exists(encodings_folder):
            os.makedirs(encodings_folder)

        # Initialize a dictionary to store known encodings
        known_encodings = {}

        # Loop over the image files in the dataset folder
        for root, dirs, files in os.walk(dataset_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_path = os.path.join(root, file)
                    name = os.path.basename(os.path.dirname(image_path))

                    try:
                        # Load the input image and convert it from BGR to RGB
                        image = cv2.imread(image_path)
                        if image is None:
                            raise Exception(f"Failed to load image: {image_path}")

                        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                        # Resize the image (adjust the size as needed)
                        rgb = cv2.resize(rgb, (224, 224))

                        # Detect the face bounding boxes in the input image
                        boxes = face_recognition.face_locations(rgb, model="hog")

                        # Compute the facial encodings for each detected face
                        encodings = face_recognition.face_encodings(rgb, boxes)

                        # Append encodings to the known_encodings dictionary
                        if name not in known_encodings:
                            known_encodings[name] = []
                        known_encodings[name].extend(encodings)

                    except Exception as image_processing_error:
                        print(f"Error processing image {image_path}: {str(image_processing_error)}")

        # Serialize the facial encodings to separate JSON files for each user
        print("[INFO] Serializing encodings...")
        for name, enc_list in known_encodings.items():
            try:
                # Serialize the list of encodings to JSON format
                encoding_json = json.dumps(enc_list, default=lambda x: x.tolist())

                # Save encodings to the database
                save_encodings_to_database(name, encoding_json)

                # Save encodings to JSON files
                encoding_filename = os.path.join(encodings_folder, f"encodings_{name}.json")
                with open(encoding_filename, 'w') as json_file:
                    json_file.write(encoding_json)

            except Exception as serialization_error:
                print(f"Error serializing and saving encodings for {name}: {str(serialization_error)}")

        return redirect(url_for('user_management'))

    except Exception as e:
        print(f"Error processing and saving encodings: {str(e)}")
        return "Error processing and saving encodings"

def save_encodings_to_database(user_id, encoding_json):
    try:
        # Establish a connection to the database
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Insert encodings into the database
        cursor.execute("INSERT INTO encodings (user_id, encoding) VALUES (%s, %s)", (user_id, encoding_json))

        # Commit the changes and close the connection
        connection.commit()
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error saving encodings to the database: {str(e)}")

@app.route('/recognition', methods=['POST'])
def start_recognition():
    # Execute the recognition.py script when the button is clicked
    subprocess.run(['python', 'recognition.py'])
    return redirect(url_for('logs'))

@app.route('/authentication-success', methods=['POST'])
def authentication_success():
    try:
        # Get the user_id from the request (you need to adapt this based on your implementation)
        user_id = request.form.get('user_id')  # Example: Extract user_id from the POST request

        # Log the successful authentication event
        log_authentication_success(user_id, "Authentication Successful")

        # You can add other actions here if needed

        return redirect(url_for('logs'))
    except Exception as e:
        # Handle any errors that may occur
        print(f"Error handling authentication success: {e}")
        return "Error handling authentication success"

@app.route('/authentication-failure', methods=['POST'])
def authentication_failure():
    try:
        # Get the user_id from the request (you need to adapt this based on your implementation)
        user_id = request.form.get('user_id')  # Example: Extract user_id from the POST request

        # Log the failed authentication event
        log_authentication_failed(user_id, "Authentication Failed")

        # You can add other actions here if needed

        return redirect(url_for('logs'))
    except Exception as e:
        # Handle any errors that may occur
        print(f"Error handling authentication failure: {e}")
        return "Error handling authentication failure"

@app.route('/about_us')
def about_us():
    return render_template('about.html')

# Route for logout
@app.route('/logout')
@login_required
def logout():
    # Clear the user's session to log them out
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
