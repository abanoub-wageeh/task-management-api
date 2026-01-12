# Task Management API

A simple task management REST API built with FastAPI.

## Database Design

![ERD Diagram](app/erd-diagram.png)

The system includes:

- **Users** - Manage user accounts
- **Tasks** - Create and track tasks

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
   cd <project-directory>
```

2. **Create a virtual environment**

   On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

   On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/task_management

# JWT Configuration
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256

# Email Configuration (Gmail)
EMAIL=your-email@gmail.com
APP_PASSWORD=your-gmail-app-password
```

> **Note**: For Gmail, you need to generate an [App Password](https://support.google.com/accounts/answer/185833) from your Google Account settings.

### 5. Run the application

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create a new user account |
| GET | `/verify` | Verify email with token |
| POST | `/login` | Login and receive access token |

## 📖 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 📁 Project Structure

```
task_managment_system/
├── main.py              # Application entry point
├── models.py            # SQLModel database models
├── schemas.py           # Pydantic request/response schemas
├── oauth2.py            # JWT token handling
├── utils.py             # Password hashing & email utilities
├── routes/
│   └── auth.py          # Authentication endpoints
├── .env                 # Environment variables (not in git)
├── requirements.txt     # Python dependencies
├── erd-diagram.png      # Database ERD diagram
└── readme.md            # This file
```
