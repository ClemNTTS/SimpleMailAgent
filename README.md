# EmailManager 📧

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

EmailManager is a modern web application for managing and automatically classifying your emails. It uses the Google Gemini API to intelligently analyze and categorize your emails.

![image](https://github.com/user-attachments/assets/e071a93e-08b4-4544-b509-9e524e6c8bdc)


## 🌟 Features

- 🔐 **Secure Authentication**

  - User registration and login
  - Route protection with authentication
  - Secure session management

- 📥 **Simplified IMAP Setup**

  - Gmail IMAP support
  - One-step configuration
  - Automatic connection testing

- 🤖 **Smart Email Management**

  - Automatic category classification
  - Content analysis with Google Gemini
  - Important email detection

- ✉️ **Email Actions**

  - Mark as read/unread
  - Delete emails
  - Mark senders as promotional

- 🎨 **Modern Interface**
  - Responsive design
  - Dark/light theme
  - Real-time notifications

## 📋 Prerequisites

- Python 3.8 or higher
- A Gmail account with two-factor authentication enabled
- A modern web browser
- A Google Gemini API key (optional)

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/emailmanager.git
   cd emailmanager
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application**
   ```bash
   flask run
   ```

## 📝 Gmail Configuration

1. **Enable two-factor authentication**

   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable two-factor authentication

2. **Create an application password**

   - In Google security settings
   - Go to "App passwords"
   - Select "Other (Custom name)"
   - Name it "EmailManager"
   - Copy the generated password

3. **Configure the application**
   - Log in to EmailManager
   - Go to settings
   - Enter your Gmail address
   - Paste the application password
   - The default IMAP server is `imap.gmail.com`

## 🔒 Security

- 🔑 Password hashing with Werkzeug
- 🛡️ Built-in CSRF protection
- 🔐 Secure session management
- 🔒 Secure API key storage
- 🚫 SQL injection protection

## 🛠️ Architecture

```
emailmanager/
├── app.py              # Application entry point
├── src/
│   ├── auth.py        # Authentication management
│   ├── mails.py       # Email handling
│   ├── agent.py       # Artificial intelligence
│   └── db.py          # Database management
├── frontend/
│   ├── static/
│   │   ├── css/       # CSS styles
│   │   └── js/        # JavaScript scripts
│   └── templates/     # HTML templates
└── requirements.txt   # Python dependencies
```

## 📊 Database

The application uses SQLite with two main tables:

- **users**: User information storage

  - id, username, password, email, imap_password, imap_server, gemini_api_key

- **mails**: Email storage
  - id, user_id, subject, sender, date, content, category, is_read, is_pub

## 🤝 Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the project
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📫 Support

For any questions or issues:

- Open an issue on GitHub
- Contact the development team
- Check the documentation

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - Lightweight web framework
- [Google Gemini](https://ai.google.dev/) - AI API
- [Font Awesome](https://fontawesome.com/) - Icons
- The open source community

---

Made with ❤️ by a student developer
