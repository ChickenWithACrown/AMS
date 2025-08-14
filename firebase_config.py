import os
import pyrebase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if not self.initialized:
            try:
                # Firebase configuration
                self.config = {
                    "apiKey": os.getenv("FIREBASE_API_KEY"),
                    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
                    "databaseURL": os.getenv("FIREBASE_DATABASE_URL"),
                    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
                    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
                    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
                    "appId": os.getenv("FIREBASE_APP_ID"),
                    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID")
                }
                
                # Initialize Firebase
                self.firebase = pyrebase.initialize_app(self.config)
                
                # Get references to services
                self.auth = self.firebase.auth()
                self.db = self.firebase.database()
                self.storage = self.firebase.storage()
                
                self.initialized = True
                print("Firebase client SDK initialized successfully")
                
            except Exception as e:
                print(f"Error initializing Firebase client SDK: {e}")
                raise
    
    def sign_in_with_email_password(self, email, password):
        try:
            if not email or not password:
                raise ValueError("Email and password are required")
                
            # Sign in with email and password
            user = self.auth.sign_in_with_email_and_password(email, password)
            
            # Get additional user data
            user_info = self.auth.get_account_info(user['idToken'])
            
            # Format user data consistently
            user_data = {
                'uid': user['localId'],
                'email': user['email'],
                'email_verified': user_info['users'][0].get('emailVerified', False),
                'display_name': user_info['users'][0].get('displayName', ''),
                'photo_url': user_info['users'][0].get('photoUrl', '')
            }
            
            # Store the refresh token for session management
            user_data['refresh_token'] = user.get('refreshToken', '')
            
            return user_data
            
        except Exception as e:
            error_msg = str(e)
            if "INVALID_EMAIL" in error_msg:
                error_msg = "Invalid email address"
            elif "MISSING_PASSWORD" in error_msg:
                error_msg = "Password is required"
            elif "TOO_MANY_ATTEMPTS_TRY_LATER" in error_msg:
                error_msg = "Too many failed attempts. Please try again later."
            elif "INVALID_PASSWORD" in error_msg:
                error_msg = "Invalid password"
            
            raise Exception(f"Authentication error: {error_msg}")
        except Exception as e:
            raise Exception(f"Unexpected error during sign in: {str(e)}")
    
    def create_user_with_email_password(self, email, password, user_data=None):
        try:
            # Create user with email and password
            user = self.auth.create_user_with_email_and_password(email, password)
            
            # Get the user's ID token and refresh token
            user_info = self.auth.get_account_info(user['idToken'])
            
            # Prepare user data to store in the database
            if user_data is None:
                user_data = {}
                
            # Add standard fields
            user_data.update({
                'email': email,
                'created_at': {
                    '.sv': 'timestamp'  # Firebase server timestamp
                },
                'email_verified': False,
                'last_login': {
                    '.sv': 'timestamp'
                }
            })
            
            # Store additional user data in the database
            self.db.child("users").child(user['localId']).set(user_data)
            
            # Format the return value consistently with sign_in_with_email_password
            result = {
                'uid': user['localId'],
                'email': user['email'],
                'email_verified': False,
                'display_name': user_data.get('display_name', ''),
                'photo_url': user_data.get('photo_url', ''),
                'refresh_token': user.get('refreshToken', '')
            }
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            if 'EMAIL_EXISTS' in error_msg:
                raise ValueError("An account with this email already exists")
            elif 'WEAK_PASSWORD' in error_msg:
                raise ValueError("Password should be at least 6 characters")
            elif 'INVALID_EMAIL' in error_msg:
                raise ValueError("Invalid email address")
            else:
                raise Exception(f"Error creating user: {error_msg}")
    
    def send_password_reset_email(self, email):
        try:
            self.auth.send_password_reset_email(email)
            return True
        except Exception as e:
            error_msg = str(e)
            if 'INVALID_EMAIL' in error_msg:
                raise ValueError("Invalid email address")
            elif 'MISSING_EMAIL' in error_msg:
                raise ValueError("Email is required")
            elif 'EMAIL_NOT_FOUND' in error_msg:
                raise ValueError("No user found with this email address")
            else:
                raise Exception(f"Error sending password reset email: {error_msg}")
    
    def get_user(self, id_token):
        try:
            user_info = self.auth.get_account_info(id_token)
            if not user_info or 'users' not in user_info or not user_info['users']:
                raise ValueError("User not found")
                
            user = user_info['users'][0]
            return {
                'uid': user.get('localId', ''),
                'email': user.get('email', ''),
                'email_verified': user.get('emailVerified', False),
                'display_name': user.get('displayName', ''),
                'photo_url': user.get('photoUrl', ''),
                'last_login_at': user.get('lastLoginAt', ''),
                'created_at': user.get('createdAt', '')
            }
        except Exception as e:
            error_msg = str(e)
            if 'INVALID_ID_TOKEN' in error_msg:
                raise ValueError("Invalid or expired authentication token")
            else:
                raise Exception(f"Error getting user: {error_msg}")
    
    def refresh_token(self, refresh_token):
        try:
            # In Firebase client SDK, we can use the refresh token to get a new ID token
            user = self.auth.refresh(refresh_token)
            return {
                'id_token': user['idToken'],
                'refresh_token': user.get('refreshToken', refresh_token),  # Use new refresh token if provided
                'expires_in': user.get('expiresIn', 3600),
                'user_id': user.get('userId', '')
            }
        except Exception as e:
            error_msg = str(e)
            if 'TOKEN_EXPIRED' in error_msg or 'INVALID_REFRESH_TOKEN' in error_msg:
                raise ValueError("Invalid or expired refresh token")
            else:
                raise Exception(f"Error refreshing token: {error_msg}")
    
    def get_data(self, path):
        try:
            return self.db.child(path).get().val()
        except Exception as e:
            print(f"Error getting data: {e}")
            raise
    
    def set_data(self, path, data):
        try:
            self.db.child(path).set(data)
            return True
        except Exception as e:
            print(f"Error setting data: {e}")
            raise
    
    def update_data(self, path, updates):
        try:
            self.db.child(path).update(updates)
            return True
        except Exception as e:
            print(f"Error updating data: {e}")
            raise
    
    def delete_data(self, path):
        try:
            self.db.child(path).remove()
            return True
        except Exception as e:
            print(f"Error deleting data: {e}")
            raise
    
    def upload_file(self, file_path, storage_path):
        try:
            self.storage.child(storage_path).put(file_path)
            return self.storage.child(storage_path).get_url(None)
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise
    
    def download_file(self, storage_path, local_path):
        try:
            self.storage.child(storage_path).download(local_path)
            return True
        except Exception as e:
            print(f"Error downloading file: {e}")
            raise
    
    def delete_file(self, storage_path):
        try:
            self.storage.child(storage_path).delete()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            raise
    
    def create_user(self, email, password, user_data=None):
        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            
            if user_data:
                self.db.child("users").child(user['localId']).set(user_data)
                
            return user
        except Exception as e:
            print(f"Error creating user: {e}")
            raise
    
    def update_user_data(self, user_id, data):
        try:
            self.db.child("users").child(user_id).update(data)
            return True
        except Exception as e:
            print(f"Error updating user data: {e}")
            return False
    
    def get_user_data(self, user_id):
        try:
            return self.db.child("users").child(user_id).get().val()
        except Exception as e:
            print(f"Error getting user data: {e}")
            return None
    
    def get_collection(self, collection_path):
        try:
            return self.db.child(collection_path).get().val()
        except Exception as e:
            print(f"Error getting collection {collection_path}: {e}")
            return None
    
    def add_document(self, collection_path, data):
        try:
            return self.db.child(collection_path).push(data)
        except Exception as e:
            print(f"Error adding document to {collection_path}: {e}")
            raise
    
    def update_document(self, document_path, data):
        try:
            self.db.child(document_path).update(data)
            return True
        except Exception as e:
            print(f"Error updating document {document_path}: {e}")
            return False
    
    def delete_document(self, document_path):
        try:
            self.db.child(document_path).remove()
            return True
        except Exception as e:
            print(f"Error deleting document {document_path}: {e}")
            return False
