# 📚 BookMate

A web-based platform designed to help readers log, rate, and track their books with personalized recommendations and community features.

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Latest-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Integration](#api-integration)
- [Deployment](#deployment)
- [Team](#team)
- [Acknowledgments](#acknowledgments)

---

## 🎯 About the Project

**BookMate** is a comprehensive book tracking and recommendation platform that addresses the challenges readers face in managing their reading habits across multiple platforms. Unlike basic book logging tools, BookMate offers:

- **Detailed Progress Tracking**: Save your last-read page and never lose your place
- **Personalized Recommendations**: Discover books based on your favorite genres and tags
- **Direct Purchase Links**: Seamlessly continue reading or purchase books
- **Community Engagement**: Participate in reading challenges and discussions
- **Comprehensive Analytics**: Track your reading habits and achievements

### Problem Statement

Many readers struggle with:
- Limited bookmarking features for tracking reading progress
- Generic, non-personalized book recommendations
- Lack of direct links to continue or purchase books
- Limited community engagement features

BookMate solves these issues by combining detailed analytics, tailored recommendations, and community participation to create an enhanced reading experience.

---

## ✨ Key Features

### 📖 Book Management
- **Book Logging**: Add books to your personal library
- **Progress Tracking**: Save and update your current page for each book
- **Favorites**: Mark books as favorites for quick access
- **Ratings**: Rate books and view your reading history
- **Tags**: Organize books with custom tags

### 🔍 Discovery
- **Book Search**: Search for books using the Open Library API
- **Genre Filtering**: Filter books by genre and tags
- **Personalized Recommendations**: Get book suggestions based on your reading preferences
- **Book Preview**: View detailed information, descriptions, and cover images

### 👤 User Features
- **User Profiles**: Customize your profile with profile pictures (Supabase storage)
- **Reading Statistics**: Track your reading progress and achievements
- **Purchase History**: View your book purchase history
- **Profile Customization**: Update your reading preferences and personal information

### 🛒 Purchase Integration
- **Direct Purchase Links**: Buy books from multiple online retailers
- **Purchase Tracking**: Keep a record of purchased books

### 📱 Reader Experience
- **Book Reader**: Read books directly in the platform
- **Responsive Design**: Optimized for desktop and mobile browsers

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 5.2.6
- **Language**: Python 3.13+
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: Django Authentication System
- **API Integration**: Open Library API
- **Cloud Storage**: Supabase (profile pictures)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Custom styling with responsive design
- **JavaScript (ES6)**: Modular JavaScript for dynamic functionality
- **AJAX**: Asynchronous data fetching

### Deployment & Infrastructure
- **Web Server**: Gunicorn
- **Static Files**: WhiteNoise
- **Platform**: Render
- **Database**: PostgreSQL (Supabase)
- **Version Control**: Git/GitHub

### Key Python Packages
```
Django==5.2.6
psycopg2-binary==2.9.10
gunicorn==21.2.0
whitenoise==6.11.0
supabase==2.10.0
python-dotenv==1.1.1
requests==2.32.5
dj-database-url==3.0.1
```

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.13+**: [Download Python](https://www.python.org/downloads/)
- **PostgreSQL**: [Download PostgreSQL](https://www.postgresql.org/download/) or use [Supabase](https://supabase.com/)
- **Git**: [Download Git](https://git-scm.com/downloads)
- **pip**: Python package installer (comes with Python)

### Installation

1. **Clone the repository**
   ```powershell
   git clone https://github.com/DaveC020/BookMate.git
   cd BookMate
   ```

2. **Create and activate virtual environment**
   ```powershell
   python -m venv env
   .\env\Scripts\Activate.ps1
   ```
   
   *Note: On Unix/Linux, use `source env/bin/activate`*

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

### Environment Variables

Create a `.env` file in the project root directory:

```env
# Database Configuration (Supabase PostgreSQL)
DATABASE_URL=postgresql://username:password@host:port/database_name

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_BUCKET=profile-pictures

# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1,bookmate-ya2p.onrender.com
```

**Important**: 
- Never commit the `.env` file to version control
- Generate a new SECRET_KEY for production using: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

### Database Setup

1. **Run migrations**
   ```powershell
   cd BookMate
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create a superuser (admin account)**
   ```powershell
   python manage.py createsuperuser
   ```

3. **Load initial data (optional)**
   ```powershell
   python manage.py loaddata initial_data.json
   ```

### Running the Application

1. **Development Server**
   ```powershell
   python manage.py runserver
   ```
   
   Access the application at: `http://127.0.0.1:8000/`

2. **Admin Panel**
   
   Access the admin panel at: `http://127.0.0.1:8000/admin/`

---

## 📁 Project Structure

```
BookMate/
├── BookMate/                    # Main Django project directory
│   ├── core/                   # Project configuration
│   │   ├── settings.py        # Django settings
│   │   ├── urls.py            # Root URL configuration
│   │   └── wsgi.py            # WSGI configuration
│   ├── library/               # Book management app
│   │   ├── models.py          # UserBookList, UserProfile models
│   │   ├── views_new.py       # Dashboard, search, book management views
│   │   ├── urls.py            # Library URL patterns
│   │   └── migrations/        # Database migrations
│   ├── home/                  # Landing page app
│   ├── login/                 # Authentication (login) app
│   ├── sign_up/               # User registration app
│   ├── profile_page/          # User profile management app
│   ├── purchase/              # Book purchase tracking app
│   ├── reader/                # Book reader interface app
│   ├── genre_setup/           # Genre selection/setup app
│   ├── static/                # Static files (CSS, JS, images)
│   │   ├── css/               # Stylesheets
│   │   ├── js/                # JavaScript modules
│   │   │   ├── dashboard.js   # Dashboard functionality
│   │   │   ├── purchase-new.js # Purchase handling
│   │   │   └── utils/         # Utility functions
│   │   └── images/            # Image assets
│   ├── templates/             # HTML templates
│   │   ├── dashboard.html     # User dashboard
│   │   ├── landing.html       # Landing page
│   │   ├── profile.html       # User profile
│   │   ├── login.html         # Login page
│   │   ├── register.html      # Registration page
│   │   └── reader.html        # Book reader
│   └── manage.py              # Django management script
├── env/                       # Virtual environment
├── .env                       # Environment variables (not in repo)
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 💡 Usage

### For Users

1. **Sign Up / Login**
   - Create an account or log in with existing credentials
   - Set up your reading preferences and genres

2. **Add Books**
   - Search for books using the search bar
   - Add books to your library from search results or recommendations

3. **Track Your Reading**
   - Update your current page as you read
   - Mark books as favorites
   - Rate completed books

4. **Discover New Books**
   - Use genre filters to find books matching your interests
   - Explore personalized recommendations based on your library

5. **Manage Your Profile**
   - Upload a profile picture
   - View your reading statistics
   - Check your purchase history

### For Administrators

1. **Access Admin Panel**
   - Navigate to `/admin/`
   - Log in with superuser credentials

2. **Manage Content**
   - View and moderate user accounts
   - Monitor book entries and user activity
   - Manage system settings

---

## 🔌 API Integration

### Open Library API

BookMate integrates with the [Open Library API](https://openlibrary.org/developers/api) for:

- **Book Search**: Search millions of books by title, author, or ISBN
- **Book Details**: Fetch comprehensive book information
- **Cover Images**: Display book cover thumbnails and full-size images
- **Purchase Links**: Provide links to online retailers

**Example API Endpoints Used:**
- Search: `https://openlibrary.org/search.json?q={query}`
- Book Details: `https://openlibrary.org/works/{work_id}.json`
- Cover Images: `https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg`

---

## 🌐 Deployment

### Deploying to Render

1. **Prepare for Deployment**
   - Ensure `DEBUG=False` in production settings
   - Configure `ALLOWED_HOSTS` with your domain
   - Set up environment variables in Render dashboard

2. **Deploy**
   - Connect your GitHub repository to Render
   - Configure build command: `pip install -r requirements.txt`
   - Configure start command: `cd BookMate && gunicorn core.wsgi:application`

3. **Database**
   - Use Supabase PostgreSQL or Render PostgreSQL
   - Run migrations after deployment: `python manage.py migrate`

4. **Static Files**
   - WhiteNoise automatically serves static files in production
   - Run `python manage.py collectstatic` if needed

**Live Deployment**: [https://bookmate-ya2p.onrender.com](https://bookmate-ya2p.onrender.com)

---

## 👥 Team

### IT317-G5 Project Team

**Product Owner**
- **Dharell Dave H. Melliza** - Project vision and stakeholder management

**Scrum Master**
- **Kaysean Miel** - Agile process facilitation and team coordination

**Business Analyst**
- **Jhondy Dain Mantilla** - Requirements analysis and documentation

**Development Team**
- **Russjie Guinto Hopista** - Full Stack Developer
- **Dien Michael Miao Laurente** - Full Stack Developer
- **Jhon Gil Vergaral Lauro** - Full Stack Developer

### Instructors
- **Joemarie Amparo** - IT317 Course Instructor
- **Frederick Revilleza** - CSIT327 Course Instructor

---

## 🎓 Acknowledgments

This project was developed as part of the **IT317** course curriculum. Special thanks to:

- Our instructors for their guidance and support
- The Django and Python communities for excellent documentation
- Open Library for providing free access to book data
- Supabase for cloud storage and database services
- All beta testers and early users for their valuable feedback

### References

- Huang & Liang (2015) - Digital reading behavior and engagement studies
- Speciale, Vallero, Vassio, & Mellia (2023) - Recommendation systems in digital platforms
- Pardede, Rafli, & Iskandar (2023) - Digital reading platform usability research

---

## 📄 License

This project is developed for educational purposes as part of the IT317 course.

---

## 📞 Contact & Support

For questions, suggestions, or issues:

- **GitHub Issues**: [Create an issue](https://github.com/DaveC020/BookMate/issues)
- **Project Repository**: [https://github.com/DaveC020/BookMate](https://github.com/DaveC020/BookMate)

---

## 🔄 Project Status

**Current Version**: Beta (Q4 2025)
**Target Launch**: December 2025

### Development Roadmap
- [x] Core book logging and tracking features
- [x] User authentication and profiles
- [x] Open Library API integration
- [x] Purchase tracking system
- [x] Responsive UI/UX design
- [x] Book reader interface
- [ ] Community features (reading challenges)
- [ ] Advanced recommendation algorithms
- [ ] Mobile app development

---

**Made with ❤️ by the BookMate Team | © 2025**