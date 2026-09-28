# EVCharge – Smart EV Charging Station Management System

EVCharge is a web-based Smart EV Charging Station Management System developed using Python Flask, SQLite, HTML, CSS and JavaScript.

The system allows users to register, log in, search charging stations, book charging slots, view booking history and cancel bookings. An admin module is provided to manage charging stations and monitor basic system statistics.

## Features

### User Features
- User Registration
- User Login and Logout
- Charging Station Listing
- Search and Filter Charging Stations
- Charging Slot Booking
- My Bookings / Booking History
- Booking Cancellation
- Session-based Authentication

### Admin Features
- Admin Dashboard
- Total Users, Stations and Bookings Statistics
- Add Charging Station
- Delete Charging Station
- View Recent Bookings

### DevOps Features
- Agile project management using Jira
- Source code management using GitHub
- Docker containerization
- Docker image creation
- Docker container deployment

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| SQLite | Database |
| HTML | Frontend Structure |
| CSS | UI Styling |
| JavaScript | Frontend Interaction |
| Git | Version Control |
| GitHub | Source Code Repository |
| Jira | Agile Project Management |
| Docker | Containerization and Deployment |

## Project Workflow

Jira → GitHub → Docker Build → Docker Image → Docker Container → EVCharge

## Project Structure

```text
EVCharge/
│
├── app.py
├── requirements.txt
├── Dockerfile
├── .gitignore
├── README.md
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── auth.html
    ├── dashboard.html
    ├── stations.html
    ├── book.html
    └── admin.html