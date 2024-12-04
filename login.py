from base64 import b64decode
import face_recognition as fr
import time
import os
import pickle

def login_check(email, image):
    try:
        # Split the image string into header and encoded image data
        header, encoded = image.split(",", 1)

        # Generate unique filenames using the current timestamp
        current_time = str(time.time_ns())
        file_new = f"{current_time}_uploaded.png"
        file_exist = f"{current_time}_existing.png"

        # Decode and save the uploaded image
        with open(file_new, "wb") as f:
            f.write(b64decode(encoded))

        # Load the stored data
        try:
            with open("data.pickle", "rb") as f:
                data = pickle.load(f)
        except FileNotFoundError:
            return "Error: data.pickle file not found."

        # Check if the email exists in the data
        if email not in data:
            return f"Error: Email {email} not found in the database."

        # Decode and save the existing image from the database
        with open(file_exist, "wb") as f:
            f.write(b64decode(data[email]))

        try:
            # Load the images
            got_image = fr.load_image_file(file_new)
            existing_image = fr.load_image_file(file_exist)

            # Get face encodings
            got_image_facialfeatures = fr.face_encodings(got_image)
            existing_image_facialfeatures = fr.face_encodings(existing_image)

            if len(got_image_facialfeatures) == 0:
                return "Error: No face found in the uploaded image."
            if len(existing_image_facialfeatures) == 0:
                return "Error: No face found in the existing image from the database."

            # Compare faces
            results = fr.compare_faces([existing_image_facialfeatures[0]], got_image_facialfeatures[0])
            face_match = results[0]

            # Clean up the image files
            os.remove(file_new)
            os.remove(file_exist)

            if face_match:
                return "Successfully Logged in!"
            else:
                return "Failed to Log in!"
        except Exception as e:
            os.remove(file_new)
            os.remove(file_exist)
            return f"Image processing error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"
