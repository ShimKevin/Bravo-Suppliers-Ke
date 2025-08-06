import os
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from bs4 import BeautifulSoup
import requests
import uuid
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import or_, text

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'postgresql://user:password@localhost/didi')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static/uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SCRAPED_IMAGES'] = os.path.join(os.path.dirname(__file__), 'static/scraped_images')

# Email configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ('true', '1', 't')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Security settings
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
app.config['SESSION_COOKIE_HTTPONLY'] = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'

# Configure logging
app.logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
app.logger.addHandler(handler)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
mail = Mail(app)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SCRAPED_IMAGES'], exist_ok=True)

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    image = db.Column(db.String(200), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_scraped = db.Column(db.Boolean, default=False)
    original_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)  # Soft deletion flag

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='cart_items')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

class HeroMiddle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(200), nullable=True)
    discount_percentage = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HeroBanner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Updated to allow multiple images per category
class CategoryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HotSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')
    image = db.Column(db.String(200), nullable=True)

def migrate_database():
    """Add new columns to existing tables without data loss"""
    with app.app_context():
        inspector = db.inspect(db.engine)
        
        # For PostgreSQL, we'll use conditional checks instead of try/except
        columns = inspector.get_columns('hero_middle')
        column_names = [col['name'] for col in columns]
        
        # Check if discount_percentage column exists in HeroMiddle
        if 'discount_percentage' not in column_names:
            db.session.execute(text('ALTER TABLE hero_middle ADD COLUMN discount_percentage FLOAT DEFAULT 0.0'))
            print("Added discount_percentage to HeroMiddle")
        else:
            print("discount_percentage already exists in HeroMiddle")
        
        # Check if image column exists in HotSale
        columns = inspector.get_columns('hot_sale')
        column_names = [col['name'] for col in columns]
        if 'image' not in column_names:
            db.session.execute(text('ALTER TABLE hot_sale ADD COLUMN image VARCHAR(200)'))
            print("Added image to HotSale")
        else:
            print("image column already exists in HotSale")
        
        # Modify hero_middle columns to allow NULL
        hero_middle_columns = inspector.get_columns('hero_middle')
        for col in hero_middle_columns:
            if col['name'] == 'image' and not col['nullable']:
                db.session.execute(text('ALTER TABLE hero_middle ALTER COLUMN image DROP NOT NULL'))
                print("Modified hero_middle.image to allow NULL")
            if col['name'] == 'title' and not col['nullable']:
                db.session.execute(text('ALTER TABLE hero_middle ALTER COLUMN title DROP NOT NULL'))
                print("Modified hero_middle.title to allow NULL")
            if col['name'] == 'description' and not col['nullable']:
                db.session.execute(text('ALTER TABLE hero_middle ALTER COLUMN description DROP NOT NULL'))
                print("Modified hero_middle.description to allow NULL")
        
        # Modify hero_banner.image to allow NULL
        hero_banner_columns = inspector.get_columns('hero_banner')
        for col in hero_banner_columns:
            if col['name'] == 'image' and not col['nullable']:
                db.session.execute(text('ALTER TABLE hero_banner ALTER COLUMN image DROP NOT NULL'))
                print("Modified hero_banner.image to allow NULL")
                break
        
        # Create new CategoryImage table if it doesn't exist
        if not inspector.has_table('category_image'):
            db.create_all()
            print("Created category_image table")
        
        # Add is_active column to Product table if it doesn't exist
        columns = inspector.get_columns('product')
        column_names = [col['name'] for col in columns]
        if 'is_active' not in column_names:
            db.session.execute(text('ALTER TABLE product ADD COLUMN is_active BOOLEAN DEFAULT TRUE'))
            print("Added is_active to Product")
        else:
            print("is_active already exists in Product")
        
        # Commit all changes
        db.session.commit()

def create_initial_categories():
    """Create initial categories only if they don't exist"""
    # Define all categories and subcategories
    categories = [
        {'name': 'Audio Electricals', 'children': [
            'Home Theatres', 'Party Speakers', 'Sound Bars', 'TVs', 'Woofers/Subwoofers'
        ]},
        {'name': 'Kitchenware', 'children': [
            'Blenders', 'Coffee Makers', 'Microwaves', 'Toasters', 'Food Processors'
        ]},
        {'name': 'Car Essentials', 'children': [
            'Car Jacks', 'Jump Starters', 'Car Chargers', 'Car Audio', 'GPS Systems'
        ]},
        {'name': 'Gym Equipments', 'children': [
            'Treadmills', 'Dumbbells', 'Yoga Mats', 'Resistance Bands', 'Exercise Bikes'
        ]},
        {'name': 'Solar Lights', 'children': [
            'Solar Garden Lights', 'Solar Street Lights', 'Solar Flood Lights', 'Solar Lanterns', 'Solar Panels'
        ]},
        {'name': 'Home Decor', 'children': [
            'Wall Art', 'Vases', 'Candles', 'Curtains', 'Rugs'
        ]},
        {'name': 'Commercial Kitchen', 'children': []},
        {'name': 'Computing', 'children': []},
        {'name': 'Cookers', 'children': []},
        {'name': 'Coolers', 'children': []},
        {'name': 'Households', 'children': []},
        {'name': 'Washing Machines', 'children': []},
        {'name': 'Home Appliances', 'children': []},
        {'name': 'Home Security', 'children': []},
    ]
    
    created = False
    for cat_data in categories:
        # Check if category exists
        parent = Category.query.filter_by(name=cat_data['name']).first()
        if not parent:
            parent = Category(name=cat_data['name'])
            db.session.add(parent)
            db.session.flush()
            print(f"Added category: {cat_data['name']}")
            created = True
        
        # Create subcategories
        for child_name in cat_data['children']:
            child = Category.query.filter_by(name=child_name).first()
            if not child:
                child = Category(name=child_name, parent_id=parent.id)
                db.session.add(child)
                print(f"Added subcategory: {child_name} under {cat_data['name']}")
                created = True
    
    if created:
        db.session.commit()
        print("Created initial categories")
    else:
        print("All categories already exist")

# Initialize database
with app.app_context():
    db.create_all()
    
    # Run database migrations for schema changes
    migrate_database()
    
    # Create admin user from environment variables
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    # Only create admin if both credentials are provided
    if admin_username and admin_password:
        admin_user = User.query.filter_by(username=admin_username).first()
        
        if not admin_user:
            admin = User(
                username=admin_username,
                password=generate_password_hash(admin_password),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created from environment variables")
        elif not admin_user.is_admin:
            admin_user.is_admin = True
            db.session.commit()
            print("Existing user promoted to admin")
        else:
            print("Admin user already exists")
    else:
        print("Warning: ADMIN_USERNAME and/or ADMIN_PASSWORD environment variables not set. Admin user not created.")
    
    # Create default categories if they don't exist
    create_initial_categories()

# Custom decorator for admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Login Manager
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Helper Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Add cache-busting to image URLs
def get_image_url(filename):
    """Generate full URL for an image filename with cache-busting"""
    if filename:
        return url_for('static', filename=f'uploads/{filename}', v=datetime.now().timestamp())
    return None

def get_cart_count():
    if current_user.is_authenticated and not current_user.is_admin:
        return Cart.query.filter_by(user_id=current_user.id).count()
    elif 'cart' in session:
        return len(session['cart'])
    return 0

def get_cart_total():
    total = 0.0
    discounts = 0.0
    
    if current_user.is_authenticated and not current_user.is_admin:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            product = db.session.get(Product, item.product_id)
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                total += discounted_price * item.quantity
                discounts += (product.price * (product.discount / 100)) * item.quantity
    elif 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                total += discounted_price * quantity
                discounts += (product.price * (product.discount / 100)) * quantity
    return total, discounts

def generate_order_number():
    now = datetime.now()
    return f"BRAVO-{now.strftime('%Y%m%d%H%M%S')}"

def download_image(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Generate unique filename
            ext = url.split('.')[-1].lower()
            if ext not in app.config['ALLOWED_EXTENSIONS']:
                ext = 'jpg'
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(folder, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
        return None
    except Exception as e:
        app.logger.error(f"Error downloading image: {e}")
        return None

def send_order_email(order, order_items):
    try:
        subject = "New Order Received - Bravo Suppliers Ke."
        recipients = [
            app.config['MAIL_USERNAME'],  # Admin email
            order.email                   # Customer email
        ] if order.email else [app.config['MAIL_USERNAME']]
        
        # Calculate subtotal
        subtotal = sum(item.quantity * item.price for item in order_items)
        
        body = f"""
        <h2>New Order #{order.order_number}</h2>
        <p><strong>Customer:</strong> {order.first_name} {order.last_name}</p>
        <p><strong>Phone:</strong> {order.phone}</p>
        <p><strong>Email:</strong> {order.email or 'N/A'}</p>
        <p><strong>Delivery Address:</strong> {order.address}</p>
        <p><strong>Notes:</strong> {order.notes or 'None'}</p>
        
        <h3>Order Summary</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px; border: 1px solid #ddd;">Product</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Qty</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Price</th>
                <th style="padding: 8px; border: 1px solid #ddd;">Subtotal</th>
            </tr>
            {"".join(
                f'<tr><td style="padding: 8px; border: 1px solid #ddd;">{item.product.name}</td>'
                f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{item.quantity}</td>'
                f'<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">KSh {item.price:.2f}</td>'
                f'<td style="padding: 8px; border: 1px solid #ddd; text-align: right;">KSh {item.quantity * item.price:.2f}</td></tr>'
                for item in order_items
            )}
        </table>
        
        <p><strong>Subtotal:</strong> KSh {subtotal:.2f}</p>
        <p><strong>Delivery Fee:</strong> KSh 300.00</p>
        <p><strong>Total Amount:</strong> KSh {order.total_amount:.2f}</p>
        
        <p>Thank you for choosing Bravo Suppliers Ke.!</p>
        """
        
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=body,
            sender=app.config['MAIL_DEFAULT_SENDER']  # Explicit sender
        )
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Email sending failed: {str(e)}")
        return False

# Helper function to get HotSale images
def get_hot_sale_image(hot_sale):
    # Return no-image if product is inactive
    if not hot_sale.product or not hot_sale.product.is_active:
        return url_for('static', filename='images/no-image.png', _external=True)
    if hot_sale.image:
        return get_image_url(hot_sale.image)
    elif hot_sale.product and hot_sale.product.image:
        return get_image_url(hot_sale.product.image)
    return url_for('static', filename='images/no-image.png', _external=True)

# Helper function to get categories in hierarchical order for dropdowns
def get_hierarchical_categories():
    """Get categories in hierarchical order with depth information"""
    all_categories = Category.query.all()
    
    # Create a mapping of parent IDs to children
    children_map = {}
    for category in all_categories:
        if category.parent_id not in children_map:
            children_map[category.parent_id] = []
        children_map[category.parent_id].append(category)
    
    # Recursive function to build the hierarchy
    def build_tree(parent_id, depth=0):
        categories = []
        if parent_id in children_map:
            for child in children_map[parent_id]:
                categories.append((child.id, child.name, depth))
                # Add children recursively
                categories.extend(build_tree(child.id, depth + 1))
        return categories
    
    # Start with top-level categories (parent_id = None)
    return build_tree(None)

# Context processor to make common data available in all templates
@app.context_processor
def inject_common_data():
    # Get top-level categories (parent_id is None)
    top_categories = Category.query.filter_by(parent_id=None).all()
    
    # For each top category, get its direct children
    for category in top_categories:
        category.children = Category.query.filter_by(parent_id=category.id).all()
    
    current_year = datetime.now().year
    cart_count = get_cart_count()
    
    # Get hero section data with fallbacks
    hero_middle = HeroMiddle.query.filter_by(is_active=True).first()
    # Skip hero middle if missing critical fields
    if hero_middle and (not hero_middle.image or not hero_middle.title or not hero_middle.description):
        hero_middle = None
    
    hero_banner = HeroBanner.query.filter_by(is_active=True).first()
    # Skip hero banner if no image
    if hero_banner and not hero_banner.image:
        hero_banner = None
    
    # Get first image for each category
    category_hero_images = {}
    for category in top_categories:
        image = CategoryImage.query.filter_by(category_id=category.id).first()
        if image:
            category_hero_images[category.id] = get_image_url(image.filename)
    
    return dict(
        top_categories=top_categories,
        current_year=current_year,
        cart_count=cart_count,
        hero_middle=hero_middle,
        hero_banner=hero_banner,
        category_hero_images=category_hero_images,
        get_image_url=get_image_url  # Make available in templates
    )

# Routes
@app.route('/')
def home():
    # Get top-level categories
    top_categories = Category.query.filter_by(parent_id=None).all()

    # Get hero middle section
    hero_middle = HeroMiddle.query.filter_by(is_active=True).order_by(HeroMiddle.created_at.desc()).first()
    
    # Get hero banner
    hero_banner = HeroBanner.query.filter_by(is_active=True).order_by(HeroBanner.created_at.desc()).first()
    
    # Get hot sales with proper image handling - only active products
    hot_sales = HotSale.query.join(Product).filter(
        Product.is_active == True
    ).order_by(HotSale.position).limit(8).all()
    
    for hot_sale in hot_sales:
        hot_sale.display_image = get_hot_sale_image(hot_sale)
    
    # Prepare category products for the front page sections
    category_products = []
    for category in top_categories:
        # Get all child category IDs
        child_ids = [child.id for child in category.children]
        # Always include the main category ID
        child_ids.append(category.id)
        
        # Fetch products from these categories (only active products)
        products = Product.query.filter(
            Product.category_id.in_(child_ids),
            Product.is_active == True
        ).order_by(Product.created_at.desc()).limit(8).all()
        # Attach products to category object
        category.products = products
        category_products.append(category)

    return render_template('index.html', 
                           top_categories=top_categories,
                           hero_middle=hero_middle,
                           hero_banner=hero_banner,
                           hot_sales=hot_sales,
                           category_products=category_products)

@app.route('/admin')
@admin_required
def admin_index():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Count products (only active)
    product_count = Product.query.filter_by(is_active=True).count()
    
    # Get all categories for display
    categories = Category.query.all()
    
    # Get recent products (only active)
    products = Product.query.filter_by(is_active=True).order_by(Product.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           product_count=product_count,
                           categories=categories,
                           products=products)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password) and user.is_admin:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@admin_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

# Updated admin products route with hierarchical categories
@app.route('/admin/products', methods=['GET', 'POST'])
@admin_required
def admin_products():
    if request.method == 'POST':
        # Handle form submission
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        discount = float(request.form.get('discount', 0))
        category_id = int(request.form.get('category_id'))
        
        # Handle file upload
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
        
        product = Product(
            name=name,
            description=description,
            price=price,
            discount=discount,
            image=image,
            category_id=category_id
        )
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    # GET request handling - show all products (active and inactive)
    products = Product.query.order_by(Product.created_at.desc()).all()
    categories = get_hierarchical_categories()
    return render_template('admin/products.html', products=products, categories=categories)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.discount = float(request.form.get('discount', 0))
        product.category_id = int(request.form.get('category_id'))
        
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Delete old image if exists
                if product.image and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], product.image)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
                product.image = filename
        
        # Handle image deletion
        if 'delete_image' in request.form and request.form['delete_image'] == 'on':
            if product.image:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
                except Exception as e:
                    app.logger.error(f"Error deleting image: {e}")
                product.image = None
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
    
    categories = get_hierarchical_categories()
    return render_template('admin/edit_product.html', product=product, categories=categories)

@app.route('/admin/product/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        # Remove from HotSales when product is deleted
        HotSale.query.filter_by(product_id=product_id).delete()
        
        # Soft delete instead of hard delete
        product.is_active = False
        db.session.commit()
        flash('Product deactivated successfully!', 'success')
    else:
        flash('Product not found', 'danger')
    return redirect(url_for('admin_products'))

@app.route('/admin/product/reactivate/<int:product_id>')
@admin_required
def reactivate_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        # Reactivate product
        product.is_active = True
        db.session.commit()
        flash('Product reactivated successfully!', 'success')
    else:
        flash('Product not found', 'danger')
    return redirect(url_for('admin_products'))

# NEW: Permanent deletion route
@app.route('/admin/product/delete-permanent/<int:product_id>')
@admin_required
def delete_product_permanent(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('admin_products'))
    
    # Check if product exists in any orders
    order_item_count = OrderItem.query.filter_by(product_id=product_id).count()
    
    if order_item_count > 0:
        flash('Cannot delete product permanently because it exists in orders', 'danger')
    else:
        # Delete associated cart items
        Cart.query.filter_by(product_id=product_id).delete()
        
        # Delete associated hot sales
        HotSale.query.filter_by(product_id=product_id).delete()
        
        # Delete image file if exists
        if product.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], product.image))
            except Exception as e:
                app.logger.error(f"Error deleting image: {e}")
        
        db.session.delete(product)
        db.session.commit()
        flash('Product permanently deleted!', 'success')
    
    return redirect(url_for('admin_products'))

@app.route('/admin/hero-middle', methods=['GET', 'POST'])
@admin_required
def admin_hero_middle():
    hero_middle = HeroMiddle.query.filter_by(is_active=True).first()
    if not hero_middle:
        hero_middle = HeroMiddle(title='', description='', image=None, discount_percentage=0, is_active=True)
        db.session.add(hero_middle)
        db.session.commit()
    
    if request.method == 'POST':
        # Handle delete request
        if 'delete' in request.form:
            # Delete all fields
            hero_middle.title = None
            hero_middle.description = None
            hero_middle.discount_percentage = 0.0
            # Delete image file
            if hero_middle.image:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], hero_middle.image))
                except Exception as e:
                    app.logger.error(f"Error deleting image: {e}")
                hero_middle.image = None
            db.session.commit()
            flash('Hero section cleared successfully!', 'success')
            return redirect(url_for('admin_hero_middle'))
        
        # Update fields
        hero_middle.title = request.form.get('title')
        hero_middle.description = request.form.get('description')
        hero_middle.discount_percentage = float(request.form.get('discount_percentage', 0))
        
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Delete old image if exists
                if hero_middle.image:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], hero_middle.image))
                    except Exception as e:
                        app.logger.error(f"Error deleting old image: {e}")
                hero_middle.image = filename
        
        db.session.commit()
        flash('Hero section updated successfully!', 'success')
        return redirect(url_for('admin_hero_middle'))
    
    return render_template('admin/hero_middle.html', hero_middle=hero_middle)

# Updated admin_hero_banner route with validation
@app.route('/admin/hero-banner', methods=['GET', 'POST'])
@admin_required
def admin_hero_banner():
    hero_banner = HeroBanner.query.filter_by(is_active=True).first()
    if not hero_banner:
        hero_banner = HeroBanner(image=None, is_active=True)
        db.session.add(hero_banner)
        db.session.commit()
    
    if request.method == 'POST':
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Delete old image if exists
                if hero_banner.image:
                    try:
                        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], hero_banner.image))
                    except Exception as e:
                        app.logger.error(f"Error deleting old image: {e}")
                hero_banner.image = filename
        
        # Handle delete request
        if 'delete' in request.form:
            # Delete image file
            if hero_banner.image:
                try:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], hero_banner.image))
                except Exception as e:
                    app.logger.error(f"Error deleting image: {e}")
                hero_banner.image = None
        
        db.session.commit()
        flash('Banner updated successfully!', 'success')
        return redirect(url_for('admin_hero_banner'))
    
    return render_template('admin/hero_banner.html', hero_banner=hero_banner)

@app.route('/admin/category-images', methods=['GET', 'POST'])
@admin_required
def admin_category_images():
    categories = Category.query.filter_by(parent_id=None).all()
    
    # Create a dictionary of category_id to images
    category_images = {}
    for category in categories:
        images = CategoryImage.query.filter_by(category_id=category.id).all()
        category_images[category.id] = [get_image_url(img.filename) for img in images]
    
    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        category = Category.query.get(category_id)
        
        # Handle multiple file uploads
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files[:8]:  # Limit to 8 files
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    # Check if we've reached the 8-image limit
                    existing_count = CategoryImage.query.filter_by(category_id=category_id).count()
                    if existing_count >= 8:
                        flash('Cannot upload more than 8 images per category', 'warning')
                        break
                    
                    # Create new image record
                    category_image = CategoryImage(
                        category_id=category_id,
                        filename=filename
                    )
                    db.session.add(category_image)
            
            db.session.commit()
            flash('Category images uploaded successfully!', 'success')
            # Update the local dictionary
            images = CategoryImage.query.filter_by(category_id=category_id).all()
            category_images[category_id] = [get_image_url(img.filename) for img in images]
        else:
            flash('No files selected', 'danger')
        
        return redirect(url_for('admin_category_images'))
    
    return render_template('admin/category_images.html', 
                           categories=categories,
                           category_images=category_images)

@app.route('/admin/category-image/delete/<int:image_id>', methods=['POST'])
@admin_required
def delete_category_image(image_id):
    image = CategoryImage.query.get(image_id)
    if image:
        # Delete image file
        if image.filename and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image.filename)):
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
            except Exception as e:
                app.logger.error(f"Error deleting image: {e}")
        
        db.session.delete(image)
        db.session.commit()
        flash('Category image deleted successfully!', 'success')
    else:
        flash('Image not found', 'warning')
    return redirect(url_for('admin_category_images'))

@app.route('/admin/hot-sales', methods=['GET', 'POST'])
@admin_required
def admin_hot_sales():
    # Get current hot sales - only active products
    hot_sales = HotSale.query.join(Product).filter(
        Product.is_active == True
    ).order_by(HotSale.position).all()
    
    if request.method == 'POST':
        # Clear existing hot sales
        HotSale.query.delete()
        
        # Add new hot sales
        product_ids = request.form.getlist('product_ids[]')
        for position, product_id in enumerate(product_ids):
            if product_id:
                # Handle image upload for each hot sale
                image = None
                file_key = f'image_{position}'
                if file_key in request.files:
                    file = request.files[file_key]
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        image = filename
                
                hot_sale = HotSale(
                    product_id=int(product_id),
                    position=position,
                    image=image
                )
                db.session.add(hot_sale)
        
        db.session.commit()
        flash('Hot Sales updated successfully!', 'success')
        return redirect(url_for('admin_hot_sales'))
    
    # Get all products for selection (only active products)
    all_products = Product.query.filter_by(is_active=True).all()
    
    # Add display image to each hot sale for preview
    for hot_sale in hot_sales:
        hot_sale.display_image = get_hot_sale_image(hot_sale)
    
    return render_template('admin/hot_sales.html', 
                           hot_sales=hot_sales,
                           all_products=all_products)

@app.route('/scrape-products', methods=['GET', 'POST'])
@admin_required
def scrape_products():
    if request.method == 'POST':
        url = request.form.get('url')
        category_id = request.form.get('category_id')
        message = None
        category = None
        
        # Validate category ID
        if not category_id:
            flash('Please select a category', 'danger')
            return redirect(url_for('scrape_products'))
        
        try:
            category_id = int(category_id)
            category = Category.query.get(category_id)
            if not category:
                flash(f'Category with ID {category_id} not found', 'danger')
                return redirect(url_for('scrape_products'))
            
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example scraping logic - adjust based on target site
            products = []
            for item in soup.select('.product-item'):
                try:
                    name = item.select_one('.product-name').text.strip()
                    price_text = item.select_one('.price').text.replace('KSh', '').replace(',', '').strip()
                    price = float(price_text)
                    image_url = item.select_one('.product-image img')['src']
                    product_url = item.select_one('.product-name a')['href']
                    
                    # Download image
                    image_filename = download_image(image_url, app.config['SCRAPED_IMAGES'])
                    
                    if image_filename:
                        products.append({
                            'name': name,
                            'price': price,
                            'image': image_filename,
                            'original_url': product_url
                        })
                except Exception as e:
                    app.logger.error(f"Error scraping product: {e}")
            
            # Save products to database
            if products:
                for product_data in products:
                    product = Product(
                        name=product_data['name'],
                        price=product_data['price'],
                        image=product_data['image'],
                        category_id=category_id,
                        is_scraped=True,
                        original_url=product_data['original_url']
                    )
                    db.session.add(product)
                
                db.session.commit()
                flash(f'{len(products)} products scraped and added to {category.name} successfully!', 'success')
            else:
                flash('No products found on the page. Please check the URL and page structure.', 'warning')
                
        except Exception as e:
            app.logger.exception(f"Scraping error: {e}")
            error_msg = f'Error scraping products: {str(e)}'
            if category:
                error_msg += f' (Category: {category.name})'
            flash(error_msg, 'danger')
        
        return redirect(url_for('scrape_products'))
    
    categories = get_hierarchical_categories()
    return render_template('admin/scrape_products.html', categories=categories)

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    if request.method == 'POST':
        # Handle category creation
        name = request.form.get('name')
        parent_id = request.form.get('parent_id') or None
        
        if name:
            # Check if category already exists
            existing = Category.query.filter_by(name=name).first()
            if not existing:
                category = Category(name=name, parent_id=parent_id)
                db.session.add(category)
                db.session.commit()
                flash('Category added successfully!', 'success')
            else:
                flash('Category already exists', 'danger')
        
        return redirect(url_for('admin_categories'))
    
    # Get all categories in hierarchical order (with depth)
    hierarchical_categories = get_hierarchical_categories()
    
    # Create a dictionary of all categories for quick lookup
    all_categories = Category.query.all()
    categories_dict = {cat.id: cat for cat in all_categories}
    
    # Get all parent categories for dropdown
    parent_categories = Category.query.filter_by(parent_id=None).all()
    
    return render_template('admin/categories.html', 
                           hierarchical_categories=hierarchical_categories,
                           categories_dict=categories_dict,
                           parent_categories=parent_categories)

@app.route('/admin/category/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category:
        # Check if category has products or children
        if category.products or category.children:
            flash('Cannot delete category with products or subcategories', 'danger')
        else:
            db.session.delete(category)
            db.session.commit()
            flash('Category deleted successfully!', 'success')
    else:
        flash('Category not found', 'danger')
    return redirect(url_for('admin_categories'))

@app.route('/category/<int:category_id>')
def category(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('home'))
    
    # Get all subcategories
    subcategories = category.children
    
    # Get products in this category and all subcategories (only active products)
    category_ids = [c.id for c in category.children] + [category.id]
    products = Product.query.filter(
        Product.category_id.in_(category_ids),
        Product.is_active == True
    ).all()
    
    cart_count = get_cart_count()
    cart_total = get_cart_total()[0]
    
    return render_template('category.html',
                           category=category,
                           subcategories=subcategories,
                           products=products,
                           cart_count=cart_count,
                           cart_total=cart_total)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        flash('Product not found', 'danger')
        return redirect(url_for('home'))
    
    # Get related products from the same category (only active)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True
    ).limit(4).all()
    
    cart_count = get_cart_count()
    cart_total = get_cart_total()[0]
    
    return render_template('product_detail.html',
                           product=product,
                           related_products=related_products,
                           cart_count=cart_count,
                           cart_total=cart_total)

@app.route('/add-to-cart/<int:product_id>')
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.is_active:
        flash('Product not available', 'danger')
        return redirect(url_for('home'))
    
    if current_user.is_authenticated and not current_user.is_admin:
        # Add to database cart for authenticated users
        cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = Cart(user_id=current_user.id, product_id=product_id)
            db.session.add(cart_item)
        db.session.commit()
    else:
        # Add to session cart for guests
        if 'cart' not in session:
            session['cart'] = {}
        
        cart = session['cart']
        cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        session['cart'] = cart
    
    flash(f'{product.name} added to cart!', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/update-cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = int(request.form.get('quantity', 1))
    
    if current_user.is_authenticated and not current_user.is_admin:
        cart_item = Cart.query.get(item_id)
        if cart_item and cart_item.user_id == current_user.id:
            product = db.session.get(Product, cart_item.product_id)
            if not product or not product.is_active:
                return jsonify({'success': False, 'message': 'Product no longer available'})
            
            if quantity > 0:
                cart_item.quantity = quantity
                db.session.commit()
                flash('Cart updated successfully!', 'success')
                return jsonify({
                    'success': True,
                    'subtotal': get_cart_total()[0],
                    'discounts': get_cart_total()[1],
                    'total': get_cart_total()[0] + 300
                })
            else:
                db.session.delete(cart_item)
                db.session.commit()
                flash('Item removed from cart', 'info')
                return jsonify({
                    'success': True,
                    'removed': True,
                    'subtotal': get_cart_total()[0],
                    'discounts': get_cart_total()[1],
                    'total': get_cart_total()[0] + 300
                })
    else:
        # Handle session cart update for guests
        if 'cart' in session:
            cart = session['cart']
            if str(item_id) in cart:
                product = db.session.get(Product, int(item_id))
                if not product or not product.is_active:
                    del cart[str(item_id)]
                    session['cart'] = cart
                    return jsonify({
                        'success': False,
                        'removed': True,
                        'message': 'Product no longer available'
                    })
                
                if quantity > 0:
                    cart[str(item_id)] = quantity
                else:
                    del cart[str(item_id)]
                session['cart'] = cart
                flash('Cart updated successfully!', 'success')
                return jsonify({
                    'success': True,
                    'removed': quantity <= 0,
                    'subtotal': get_cart_total()[0],
                    'discounts': get_cart_total()[1],
                    'total': get_cart_total()[0] + 300
                })
    
    return jsonify({'success': False, 'message': 'Item not found'})

@app.route('/cart')
def view_cart():
    cart_items = []
    subtotal = 0.0
    discounts = 0.0
    total = 0.0
    
    if current_user.is_authenticated and not current_user.is_admin:
        # Get cart items from database for authenticated users
        cart_items_db = Cart.query.filter_by(user_id=current_user.id).all()
        for item in cart_items_db:
            product = db.session.get(Product, item.product_id)
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                subtotal += discounted_price * item.quantity
                discounts += (product.price * (product.discount / 100)) * item.quantity
                # Add product to display list
                cart_items.append({
                    'id': item.id,
                    'product': product,
                    'quantity': item.quantity
                })
    elif 'cart' in session:
        # Get cart items from session for guests
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                subtotal += discounted_price * quantity
                discounts += (product.price * (product.discount / 100)) * quantity
                cart_items.append({
                    'id': product.id,
                    'product': product,
                    'quantity': quantity
                })
    
    total = subtotal + 300  # Add delivery fee
    
    return render_template('cart.html',
                           cart_items=cart_items,
                           subtotal=subtotal,
                           discounts=discounts,
                           total=total)

@app.route('/remove-from-cart/<int:item_id>')
def remove_from_cart(item_id):
    if current_user.is_authenticated and not current_user.is_admin:
        cart_item = Cart.query.get(item_id)
        if cart_item and cart_item.user_id == current_user.id:
            db.session.delete(cart_item)
            db.session.commit()
            flash('Item removed from cart', 'info')
    else:
        # Handle session cart removal for guests
        if 'cart' in session:
            cart = session['cart']
            if str(item_id) in cart:
                del cart[str(item_id)]
                session['cart'] = cart
                flash('Item removed from cart', 'info')
    
    return redirect(url_for('view_cart'))

@app.route('/clear-cart')
def clear_cart():
    if current_user.is_authenticated and not current_user.is_admin:
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session.pop('cart', None)
    
    flash('Cart cleared', 'info')
    return redirect(url_for('view_cart'))

@app.route('/checkout')
def checkout():
    # Redirect to cart if empty
    if (current_user.is_authenticated and not current_user.is_admin and Cart.query.filter_by(user_id=current_user.id).count() == 0) or \
       (not current_user.is_authenticated and ('cart' not in session or len(session['cart']) == 0)):
        flash('Your cart is empty', 'warning')
        return redirect(url_for('view_cart'))
    
    cart_total, discounts = get_cart_total()
    total = cart_total + 300  # Delivery fee
    
    # Get cart items for display
    cart_items = []
    if current_user.is_authenticated and not current_user.is_admin:
        cart_items_db = Cart.query.filter_by(user_id=current_user.id).all()
        for item in cart_items_db:
            product = db.session.get(Product, item.product_id)
            if product and product.is_active:
                cart_items.append({
                    'product': product,
                    'quantity': item.quantity
                })
    elif 'cart' in session:
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product and product.is_active:
                cart_items.append({
                    'product': product,
                    'quantity': quantity
                })
    
    return render_template('checkout.html',
                           cart_items=cart_items,
                           subtotal=cart_total,
                           discounts=discounts,
                           total=total)

@app.route('/place-order', methods=['POST'])
def place_order():
    # Get form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    notes = request.form.get('notes')
    
    # Get cart total
    cart_total, discounts = get_cart_total()
    total = cart_total + 300  # Delivery fee
    
    # Create order
    order = Order(
        order_number=generate_order_number(),
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
        address=address,
        notes=notes,
        total_amount=total
    )
    db.session.add(order)
    db.session.flush()  # Get order ID
    
    # Add order items
    if current_user.is_authenticated and not current_user.is_admin:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            product = db.session.get(Product, item.product_id)
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=discounted_price
                )
                db.session.add(order_item)
        
        # Clear cart
        Cart.query.filter_by(user_id=current_user.id).delete()
    else:
        # Session cart for guests
        for product_id, quantity in session['cart'].items():
            product = db.session.get(Product, int(product_id))
            if product and product.is_active:
                discounted_price = product.price * (1 - (product.discount / 100))
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=discounted_price
                )
                db.session.add(order_item)
        
        # Clear session cart
        session.pop('cart', None)
    
    db.session.commit()
    
    # Get order items for email
    order_items = OrderItem.query.filter_by(order_id=order.id).all()
    
    # Send order email
    send_order_email(order, order_items)
    
    return render_template('order_success.html',
                           order_id=order.id,
                           total_amount=total,
                           delivery_address=address,
                           phone=phone,
                           email=email)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    sort_by = request.args.get('sort', 'relevance')  # Get sort parameter
    
    # Get all categories for navigation
    categories = Category.query.all()
    
    if query:
        # Search in product name and description (only active products)
        search_term = f"%{query}%"
        products = Product.query.filter(
            (Product.name.ilike(search_term)) | 
            (Product.description.ilike(search_term)),
            Product.is_active == True
        ).all()
        
        # Apply sorting
        if sort_by == 'price_low_high':
            products = sorted(products, key=lambda p: p.price)
        elif sort_by == 'price_high_low':
            products = sorted(products, key=lambda p: p.price, reverse=True)
        elif sort_by == 'name_asc':
            products = sorted(products, key=lambda p: p.name.lower())
        elif sort_by == 'name_desc':
            products = sorted(products, key=lambda p: p.name.lower(), reverse=True)
        # 'relevance' is the default, no additional sorting needed
    else:
        products = []
    
    return render_template('search_results.html', 
                           products=products, 
                           query=query,
                           categories=categories,
                           sort_by=sort_by)

# Orders view route
@app.route('/orders')
@admin_required
def view_orders():
    # Get all orders sorted by creation date (newest first)
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Calculate order counts by status
    status_counts = {
        'Pending': Order.query.filter_by(status='Pending').count(),
        'Processing': Order.query.filter_by(status='Processing').count(),
        'Shipped': Order.query.filter_by(status='Shipped').count(),
        'Delivered': Order.query.filter_by(status='Delivered').count(),
        'Cancelled': Order.query.filter_by(status='Cancelled').count()
    }
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    
    # Get recent orders (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_orders = Order.query.filter(Order.created_at >= seven_days_ago).count()
    
    # Prepare data for the view
    order_data = []
    for order in orders:
        # Get order items count
        item_count = OrderItem.query.filter_by(order_id=order.id).count()
        
        # Format created date
        created_date = order.created_at.strftime('%b %d, %Y')
        
        order_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': f"{order.first_name} {order.last_name}",
            'created_date': created_date,
            'total_amount': order.total_amount,
            'status': order.status,
            'item_count': item_count
        })
    
    return render_template('admin/orders.html', 
                           orders=order_data,
                           status_counts=status_counts,
                           total_revenue=total_revenue,
                           recent_orders=recent_orders)

# Email test route
@app.route('/test-email')
def test_email():
    try:
        msg = Message(
            subject='Test Email from Didi',
            recipients=[app.config['MAIL_USERNAME']],
            body='This is a test email to verify email configuration',
            sender=app.config['MAIL_DEFAULT_SENDER']  # Explicit sender
        )
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        app.logger.error(f"Email test failed: {str(e)}")
        return f'Error: {str(e)}'

# Static pages
@app.route('/about')
def about():
    cart_count = get_cart_count()
    cart_total = get_cart_total()[0]
    
    return render_template('about.html',
                           cart_count=cart_count,
                           cart_total=cart_total)

@app.route('/contact')
def contact():
    cart_count = get_cart_count()
    cart_total = get_cart_total()[0]
    
    return render_template('contact.html',
                           cart_count=cart_count,
                           cart_total=cart_total)

if __name__ == '__main__':
    app.run(debug=True)