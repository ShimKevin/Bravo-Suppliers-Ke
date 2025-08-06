# 🛒 Bravo Suppliers Ke. - E-commerce Platform

![Bravo Suppliers Logo](https://static/images/logo.png)

**Bravo Suppliers Ke.** is a powerful and user-friendly e-commerce platform built using **Python** and **Flask**. Designed for selling **home supplies and electronics**, it offers a modern shopping experience for customers and a robust admin backend for store management.

---

## 🚀 Features Overview

### 🧑‍💻 Customer-Facing Features
- **Product Browsing**: Navigate through categories with multi-level filtering.
- **Smart Search**: Find products using names or descriptions with sorting options.
- **Persistent Cart**: Saved for logged-in users; session-based for guests.
- **Secure Checkout**: Complete orders with delivery tracking.
- **Order Notifications**: Instant email confirmation to customers and admins.

### 🔐 Admin Capabilities
- **Dashboard Access**: Secure admin login with role-based control.
- **Product Manager**: Upload, edit, soft-delete, and organize products.
- **Categories Manager**: Create unlimited nested categories with images.
- **Content Management**: Customize hero banners, sales promos, etc.
- **Order Management**: Track order statuses and view customer details.
- **Web Scraping**: Import products with images from external websites.

---

## 🛠️ Technical Highlights

| Feature              | Description                                  |
|----------------------|----------------------------------------------|
| 🔒 Authentication     | Secure login with password hashing (Werkzeug) |
| 🧩 Flask Structure     | Modular blueprints and factory pattern        |
| 🖼️ Image Uploads      | Optimized image storage and caching           |
| 📧 Email Integration  | SMTP for order/status emails                  |
| 🗄️ PostgreSQL + ORM   | Using SQLAlchemy for clean DB interactions   |
| 📱 Responsive Design  | Mobile-first UI using Bootstrap 5            |

---

## 🧰 Tech Stack

### ⚙️ Backend
- Python 3.9+
- Flask, Flask-Login, Flask-SQLAlchemy, Flask-Mail
- PostgreSQL
- BeautifulSoup (for product scraping)

### 🎨 Frontend
- HTML5 + CSS3
- Bootstrap 5
- Jinja2 templates
- JavaScript (vanilla)

### ☁️ Deployment
- Gunicorn + Nginx
- Docker (for containerization)
- Heroku / AWS (cloud hosting)

---

## 🧪 Installation Guide

### 📋 Prerequisites
- Python 3.9+
- PostgreSQL installed
- SMTP credentials (Gmail, Outlook, etc.)
- Redis *(optional for advanced session management)*

---

### 🏗️ Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/bravo-suppliers.git
cd bravo-suppliers
Create and activate virtual environment

bash
Copy
Edit
python -m venv venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set up environment variables
Create a .env file in the root folder:

ini
Copy
Edit
SECRET_KEY=your_secret_key_here
DATABASE_URI=postgresql://user:password@localhost/bravo_suppliers
MAIL_SERVER=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your_email_password
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
UPLOAD_FOLDER=./static/uploads
Initialize the database

bash
Copy
Edit
flask db create_all
flask db migrate
Run the application

bash
Copy
Edit
flask run
🌐 Accessing the App
Interface	URL
🛍️ Customer Shop	http://localhost:5000
🔐 Admin Login	http://localhost:5000/admin/login

⚙️ Configuration Reference
Variable	Description	Example
SECRET_KEY	Flask session security key	supersecretkey123
DATABASE_URI	PostgreSQL connection string	postgresql://user:pass@localhost/dbname
MAIL_SERVER	SMTP server	smtp.gmail.com
MAIL_PORT	SMTP port	587
MAIL_USE_TLS	Use TLS encryption	True
MAIL_USERNAME	Email sender	admin@gmail.com
MAIL_PASSWORD	Email sender's password	yourpassword
UPLOAD_FOLDER	Where uploaded product images are stored	./static/uploads
ADMIN_USERNAME	Default admin login	admin
ADMIN_PASSWORD	Admin login password	SecurePassword123

📦 Admin Guide
📁 Product Management
Add/Edit/Delete products

Attach product images

Set prices, discounts, and stock status

🗂️ Category System
Create multi-level categories

Add cover/category images

Unlimited nesting support

🎨 Content Management
Customize homepage banners

Update promotional content

Manage featured sections

📦 Order Handling
View all customer orders

Track order status: Pending, Shipped, Delivered

View customer and shipping details

🕷️ Product Scraping
Import external products (name, image, price)

Automatically download and assign categories

🚀 Deployment Options
🟣 Heroku Deployment
bash
Copy
Edit
heroku create bravo-suppliers
heroku addons:create heroku-postgresql:hobby-dev

# Set config vars
heroku config:set SECRET_KEY=your_secret_key
heroku config:set MAIL_SERVER=smtp.yourprovider.com
heroku config:set MAIL_USERNAME=youremail@example.com
heroku config:set MAIL_PASSWORD=yourpassword
# etc...

git push heroku main
🐳 Docker Deployment
Build Docker image

bash
Copy
Edit
docker build -t bravo-suppliers .
Run the container

bash
Copy
Edit
docker run -d -p 5000:5000 --env-file .env bravo-suppliers
🤝 Contributing
We welcome all contributions! Here's how to get started:

bash
Copy
Edit
# Fork the repo
# Create a feature branch
git checkout -b feature/MyAmazingFeature

# Make your changes
git commit -m "Add AmazingFeature"

# Push and create a Pull Request
git push origin feature/MyAmazingFeature
📄 License
This project is licensed under the MIT License.
See the LICENSE file for more details.

📬 Support
Need help or want to suggest features?
Contact the development team at:

📧 support@bravosuppliers.co.ke

🏠 Bravo Suppliers Ke.
Your trusted partner for quality home supplies and electronics.
Built with ❤️ in Nairobi.

yaml
Copy
Edit

---

✅ **Tip for VS Code Preview**:  
Install the **Markdown Preview Enhanced** extension or press `Ctrl + Shift + V` in any `.md` file to see the styled preview.

Let me know if you want this split into different sections or auto-linked for GitHub's Table of Contents.







You said:
remove deployment part and add this repo https://github.com/ShimKevin/Bravo-Suppliers-Ke.


ChatGPT said:
Here is your updated, well-structured, and VS Code-friendly README.md for Bravo Suppliers Ke., with:

✅ Deployment sections removed
✅ Your GitHub repo added: https://github.com/ShimKevin/Bravo-Suppliers-Ke.

markdown
Copy
Edit
# 🛒 Bravo Suppliers Ke. - E-commerce Platform

![Bravo Suppliers Logo](https://static/images/logo.png)

**Bravo Suppliers Ke.** is a powerful and user-friendly e-commerce platform built using **Python** and **Flask**. Designed for selling **home supplies and electronics**, it offers a modern shopping experience for customers and a robust admin backend for store management.

🔗 **GitHub Repository:** [https://github.com/ShimKevin/Bravo-Suppliers-Ke.](https://github.com/ShimKevin/Bravo-Suppliers-Ke.)

---

## 🚀 Features Overview

### 🧑‍💻 Customer-Facing Features
- **Product Browsing**: Navigate through categories with multi-level filtering.
- **Smart Search**: Find products using names or descriptions with sorting options.
- **Persistent Cart**: Saved for logged-in users; session-based for guests.
- **Secure Checkout**: Complete orders with delivery tracking.
- **Order Notifications**: Instant email confirmation to customers and admins.

### 🔐 Admin Capabilities
- **Dashboard Access**: Secure admin login with role-based control.
- **Product Manager**: Upload, edit, soft-delete, and organize products.
- **Categories Manager**: Create unlimited nested categories with images.
- **Content Management**: Customize hero banners, sales promos, etc.
- **Order Management**: Track order statuses and view customer details.
- **Web Scraping**: Import products with images from external websites.

---

## 🛠️ Technical Highlights

| Feature              | Description                                  |
|----------------------|----------------------------------------------|
| 🔒 Authentication     | Secure login with password hashing (Werkzeug) |
| 🧩 Flask Structure     | Modular blueprints and factory pattern        |
| 🖼️ Image Uploads      | Optimized image storage and caching           |
| 📧 Email Integration  | SMTP for order/status emails                  |
| 🗄️ PostgreSQL + ORM   | Using SQLAlchemy for clean DB interactions   |
| 📱 Responsive Design  | Mobile-first UI using Bootstrap 5            |

---

## 🧰 Tech Stack

### ⚙️ Backend
- Python 3.9+
- Flask, Flask-Login, Flask-SQLAlchemy, Flask-Mail
- PostgreSQL
- BeautifulSoup (for product scraping)

### 🎨 Frontend
- HTML5 + CSS3
- Bootstrap 5
- Jinja2 templates
- JavaScript (vanilla)

---

## 🧪 Installation Guide

### 📋 Prerequisites
- Python 3.9+
- PostgreSQL installed
- SMTP credentials (Gmail, Outlook, etc.)
- Redis *(optional for advanced session management)*

---

### 🏗️ Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/ShimKevin/Bravo-Suppliers-Ke.
cd Bravo-Suppliers-Ke.
Create and activate virtual environment

bash
Copy
Edit
python -m venv venv
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set up environment variables
Create a .env file in the root folder:

ini
Copy
Edit
SECRET_KEY=your_secret_key_here
DATABASE_URI=postgresql://user:password@localhost/bravo_suppliers
MAIL_SERVER=smtp.yourprovider.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your@email.com
MAIL_PASSWORD=your_email_password
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_admin_password
UPLOAD_FOLDER=./static/uploads
Initialize the database

bash
Copy
Edit
flask db create_all
flask db migrate
Run the application

bash
Copy
Edit
flask run
🌐 Accessing the App
Interface	URL
🛍️ Customer Shop	http://localhost:5000
🔐 Admin Login	http://localhost:5000/admin/login

⚙️ Configuration Reference
Variable	Description	Example
SECRET_KEY	Flask session security key	supersecretkey123
DATABASE_URI	PostgreSQL connection string	postgresql://user:pass@localhost/dbname
MAIL_SERVER	SMTP server	smtp.gmail.com
MAIL_PORT	SMTP port	587
MAIL_USE_TLS	Use TLS encryption	True
MAIL_USERNAME	Email sender	admin@gmail.com
MAIL_PASSWORD	Email sender's password	yourpassword
UPLOAD_FOLDER	Where uploaded product images are stored	./static/uploads
ADMIN_USERNAME	Default admin login	admin
ADMIN_PASSWORD	Admin login password	SecurePassword123

📦 Admin Guide
📁 Product Management
Add/Edit/Delete products

Attach product images

Set prices, discounts, and stock status

🗂️ Category System
Create multi-level categories

Add cover/category images

Unlimited nesting support

🎨 Content Management
Customize homepage banners

Update promotional content

Manage featured sections

📦 Order Handling
View all customer orders

Track order status: Pending, Shipped, Delivered

View customer and shipping details

🕷️ Product Scraping
Import external products (name, image, price)

Automatically download and assign categories

🤝 Contributing
We welcome all contributions! Here's how to get started:

bash
Copy
Edit
# Fork the repo
# Create a feature branch
git checkout -b feature/MyAmazingFeature

# Make your changes
git commit -m "Add AmazingFeature"

# Push and create a Pull Request
git push origin feature/MyAmazingFeature
📄 License
This project is licensed under the MIT License.
See the LICENSE file for more details.

📬 Support
Need help or want to suggest features?
Contact the development team at:

📧 support@bravosuppliers.co.ke

🏠 Bravo Suppliers Ke.
Your trusted partner for quality home supplies and electronics.
Built with ❤️ in Nairobi.