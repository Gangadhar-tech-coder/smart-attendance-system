# 🎓 Smart Attendance System

> Touchless, face-recognition-powered attendance management system with real-time dashboards and automated record keeping.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![REST API](https://img.shields.io/badge/REST_API-FF6C37?style=for-the-badge&logo=postman&logoColor=white)

---

## 📌 Overview

The **Smart Attendance System** eliminates manual, paper-based attendance by using face recognition technology to automatically mark attendance in real time. Designed for educational institutions, it provides an interactive dashboard for admins and teachers to monitor attendance records efficiently.

---

## ✨ Features

- 🔍 **Touchless Attendance** — Face recognition marks attendance without physical contact
- 📊 **Real-Time Dashboard** — Live attendance statistics and class-wise summaries
- 🗂️ **Automated Record Management** — Attendance records stored and organized automatically
- 🔐 **Role-Based Authentication** — Separate access for Admin, Teacher, and Student roles
- 📋 **Academic Monitoring** — Attendance reports with percentage tracking per student
- 🌐 **REST API Integration** — Clean API endpoints for data access and integration

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Django, Django REST Framework |
| Face Recognition | `face_recognition` library (dlib-based) |
| Database | SQLite |
| Authentication | Role-based auth (Django built-in) |
| API | REST APIs via DRF |

---

## 🚀 Getting Started

### Prerequisites

```bash
Python 3.8+
pip
virtualenv (recommended)
cmake (required for dlib/face_recognition)
```

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Gangadhar-tech-coder/smart-attendance-system.git
cd smart-attendance-system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create superuser (admin)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

---

## 📁 Project Structure

```
smart-attendance-system/
├── attendance/          # Core attendance app
│   ├── models.py        # Student, Attendance models
│   ├── views.py         # Dashboard, face-recognition views
│   ├── urls.py          # URL routing
│   └── serializers.py   # DRF serializers
├── face_data/           # Stored face encodings
├── static/              # CSS, JS, images
├── templates/           # HTML templates
├── manage.py
└── requirements.txt
```

---

## 🔐 Roles

| Role | Access |
|------|--------|
| Admin | Full system control, user management |
| Teacher | Mark attendance, view class reports |
| Student | View own attendance records |

---

## 📸 How Face Recognition Works

1. Admin registers a student and captures their face via webcam
2. System encodes and stores the face embedding
3. During class, camera detects and matches faces against stored encodings
4. Matched students are marked **Present** automatically
5. Unmatched faces are flagged for manual review

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

