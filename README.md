# AFJROTC Management System (AMS)

A comprehensive management system for Air Force Junior Reserve Officer Training Corps (AFJROTC) programs. This application helps manage cadet records, events, uniforms, and other administrative tasks for AFJROTC units.

## Features

- **User Authentication**: Secure login and user management
- **Cadet Management**: Track cadet information, ranks, and achievements
- **Event Management**: Schedule and manage AFJROTC events and activities
- **Uniform Management**: Track uniform inventory and assignments
- **Attendance Tracking**: Record and monitor cadet attendance
- **Reporting**: Generate reports on cadet performance and unit statistics

## Prerequisites

- Python 3.8 or higher
- Firebase account with a project set up
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ChickenWithACrown/AMS.git
   cd AMS
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Firebase configuration:
   - Create a `.env` file in the root directory
   - Add your Firebase configuration (copy from Firebase Console)
   ```
   FIREBASE_API_KEY=your_api_key
   FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
   FIREBASE_DATABASE_URL=https://your_project_id.firebaseio.com
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
   FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   FIREBASE_APP_ID=your_app_id
   FIREBASE_MEASUREMENT_ID=your_measurement_id
   ```

## Running the Application

```bash
python main.py
```

## Project Structure

- `main.py`: Main application entry point
- `firebase_config.py`: Firebase configuration and service initialization
- `.env`: Environment variables (not committed to version control)
- `requirements.txt`: Python dependencies
- `README.md`: This file

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python and CustomTkinter
- Uses Firebase for backend services
- Developed for AFJROTC units worldwide
