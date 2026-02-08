# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities (requires teacher authentication)
- Teacher authentication with secure password hashing
- Session-based access control

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Set up teacher credentials:

   Create a `teachers.json` file in the `src` directory (you can copy from `teachers.example.json`):
   
   ```json
   {
     "teachers": {
       "teacher1": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7667LlnWhS"
     }
   }
   ```
   
   **Note**: The example hash above is for the password "example_password". Each deployment should generate unique hashes for their actual passwords.
   
   **Important**: The `teachers.json` file is excluded from version control for security. Each deployment should have its own copy with unique credentials.
   
   To generate a bcrypt hash for a password:
   
   ```python
   import bcrypt
   password = "your_password"
   hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
   print(hashed.decode('utf-8'))
   ```

3. Run the application:

   ```
   python app.py
   ```

4. Open your browser and go to:
   - Web interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## Authentication

The application uses session-based authentication for teachers:

- Teachers must log in to register or unregister students
- Students can view activities and participants without logging in
- Sessions are stored in-memory (suitable for single-process development only)

**Note**: For production use, implement:
- Shared session store (Redis, database) for multi-worker deployments
- Session expiration/TTL
- Secure session token storage

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| POST   | `/login`                                                          | Authenticate a teacher and receive a session token                  |
| POST   | `/logout?session_token={token}`                                   | Logout and invalidate session                                       |
| GET    | `/auth/check?session_token={token}`                               | Check if a session token is valid                                   |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu&session_token={token}` | Sign up for an activity (requires authentication) |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu&session_token={token}` | Unregister from an activity (requires authentication) |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
