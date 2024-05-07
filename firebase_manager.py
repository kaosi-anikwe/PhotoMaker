import os
import json
from urllib.parse import unquote
from firebase_admin import storage, credentials, initialize_app, firestore


# Create creds file if not exist
if not os.path.exists("firebase_creds.json"):
    cred_data = json.loads(os.getenv("FIREBASE_CREDS"), strict=False)
    with open("firebase_creds.json", "w") as creds_file:
        json.dump(cred_data, creds_file)

cred = credentials.Certificate("firebase_creds.json")
initialize_app(cred, {"storageBucket": "sadtalker-d67ba.appspot.com"})
bucket = storage.bucket()


def modify_url(url):
    try:
        url_parts = url.split("/")
        url_parts = url_parts[4:]
        print(url_parts)
        public_path = "%2f".join(url_parts)
        print(public_path)
        storage_bucket_url = "https://firebasestorage.googleapis.com/v0/b/sadtalker-d67ba.appspot.com"
        file_url = f"{storage_bucket_url}/o/{public_path}"
        print(f"file URL: {file_url}")
        return file_url
    except Exception as e:
        print(f"Error while modifying url: {str(e)}")
        return None


def upload_file_to_firebase(local_filepath, upload_filepath):
    try:
        blob = bucket.blob(upload_filepath)
        blob.upload_from_filename(local_filepath)
        file_url = blob.public_url
        modified_url = modify_url(file_url)
        return modified_url
    except Exception as e:
        return f"Error uploading file to firebase: {str(e)}"


def download_file_from_firebase(local_filepath, download_filepath):
    """Download a file from Firebase Storage and save it to the specified path."""
    try:
        file_name = local_filepath.split("/")[-1]
        file_name = unquote(file_name)
        blob = bucket.blob(file_name)
        blob.download_to_filename(download_filepath)
        print(f"Downloaded file from Firebase Storage: {local_filepath}")
    except Exception as e:
        return f"Error downloading file from firebase: {str(e)}"
