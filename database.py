# database.py
import sqlite3
import json
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# استخدام مسار مؤقت لـ Vercel
IS_VERCEL = os.environ.get('VERCEL', False)

if IS_VERCEL:
    DB_PATH = '/tmp/lasreina.db'
else:
    DB_PATH = 'lasreina.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DB_PATH):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # إنشاء جميع الجداول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'customer', 'owner')),
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT NOT NULL,
            national_id TEXT,
            national_id_image TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owner_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            chalet_number TEXT NOT NULL,
            chalet_card_image TEXT,
            business_name TEXT,
            business_address TEXT,
            tax_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            national_id_image TEXT,
            date_of_birth DATE,
            address TEXT,
            emergency_contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            description TEXT,
            icon TEXT,
            image TEXT DEFAULT 'default_category.jpg',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chalets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            description_ar TEXT,
            description_en TEXT,
            price_per_night INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            category_id INTEGER,
            image TEXT DEFAULT 'C1.jpg',
            location TEXT DEFAULT 'العين السخنة، السويس، مصر',
            bedrooms INTEGER DEFAULT 2,
            bathrooms INTEGER DEFAULT 2,
            max_guests INTEGER DEFAULT 6,
            amenities TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (owner_id) REFERENCES users (id),
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chalet_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chalet_id INTEGER NOT NULL,
            image TEXT NOT NULL,
            is_main BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chalet_id) REFERENCES chalets (id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chalet_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'cancelled', 'completed', 'rejected')),
            payment_method TEXT DEFAULT 'bank_transfer',
            amount INTEGER NOT NULL,
            days INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chalet_id) REFERENCES chalets (id),
            FOREIGN KEY (customer_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS booked_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chalet_id INTEGER NOT NULL,
            booking_id INTEGER NOT NULL,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chalet_id) REFERENCES chalets (id),
            FOREIGN KEY (booking_id) REFERENCES bookings (id),
            UNIQUE(chalet_id, date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owner_booked_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chalet_id INTEGER NOT NULL,
            date DATE NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chalet_id) REFERENCES chalets (id) ON DELETE CASCADE,
            UNIQUE(chalet_id, date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            phone TEXT,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed')),
            transaction_id TEXT,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings (id),
            FOREIGN KEY (customer_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            name TEXT NOT NULL,
            review TEXT NOT NULL,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id)
        )
    ''')
    
    # إدخال البيانات الافتراضية
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('ميني إيجيبت', 'Mini Egypt', 'شاليهات فاخرة بتصميم مصري أصيل', 'bi-pyramid', 'mini_egypt.jpg'),
            ('ريد كاربت', 'Red Carpet', 'شاليهات فاخرة بأسلوب هوليودي', 'bi-star', 'red_carpet.jpg'),
            ('نيو ريد كاربت', 'New Red Carpet', 'شاليهات فاخرة محدثة بأحدث التصاميم', 'bi-gem', 'new_red_carpet.jpg')
        ]
        cursor.executemany(
            '''INSERT INTO categories (name_ar, name_en, description, icon, image) 
               VALUES (?, ?, ?, ?, ?)''',
            default_categories
        )
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (username, password, role, name, email, phone, national_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin',
            generate_password_hash('admin123'),
            'admin',
            'مدير النظام',
            'admin@lasreina.com',
            '+20123456789',
            '12345678901234',
            'approved'
        ))
        
        cursor.execute('''
            INSERT INTO users (username, password, role, name, email, phone, national_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'owner',
            generate_password_hash('owner123'),
            'owner',
            'مالك قرية لاسرينا',
            'owner@lasreina.com',
            '+20123456789',
            '98765432109876',
            'approved'
        ))
        owner_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO owner_details (user_id, chalet_number, business_name)
            VALUES (?, ?, ?)
        ''', (owner_id, 'LSR-2024-001', 'قرية لاسرينا'))
        
        cursor.execute('''
            INSERT INTO users (username, password, role, name, email, phone, national_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'customer',
            generate_password_hash('customer123'),
            'customer',
            'عميل تجريبي',
            'customer@lasreina.com',
            '+20123456789',
            '12345678901234',
            'approved'
        ))
    
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات
try:
    init_db()
except Exception as e:
    print(f"⚠️ خطأ في تهيئة قاعدة البيانات: {e}")

# --- دوال إدارة المستخدمين ---

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('''
        SELECT u.*, od.chalet_number, od.business_name, od.chalet_card_image,
               cd.date_of_birth, cd.address, cd.emergency_contact
        FROM users u
        LEFT JOIN owner_details od ON u.id = od.user_id
        LEFT JOIN customer_details cd ON u.id = cd.user_id
        WHERE u.id = ?
    ''', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.*, od.chalet_number, od.business_name, od.chalet_card_image,
               cd.date_of_birth, cd.address,
               (SELECT COUNT(*) FROM chalets WHERE owner_id = u.id) as chalet_count
        FROM users u
        LEFT JOIN owner_details od ON u.id = od.user_id
        LEFT JOIN customer_details cd ON u.id = cd.user_id
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return [dict(user) for user in users]

def get_pending_users():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.*, od.chalet_number, od.business_name, od.chalet_card_image
        FROM users u
        LEFT JOIN owner_details od ON u.id = od.user_id
        WHERE u.status = 'pending' AND u.role != 'admin'
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return [dict(user) for user in users]

def approve_user(user_id, admin_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE users SET status = 'approved', approved_at = CURRENT_TIMESTAMP, approved_by = ?
        WHERE id = ?
    ''', (admin_id, user_id))
    conn.commit()
    conn.close()

def reject_user(user_id):
    conn = get_db_connection()
    conn.execute('UPDATE users SET status = "rejected" WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def create_user(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    national_id_image = data.get('national_id_image', '')
    if national_id_image and not national_id_image.startswith('uploads/'):
        national_id_image = f"uploads/{national_id_image}"
    
    cursor.execute('''
        INSERT INTO users (username, password, role, name, email, phone, national_id, national_id_image, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['username'],
        generate_password_hash(data['password']),
        data['role'],
        data['name'],
        data.get('email', ''),
        data['phone'],
        data.get('national_id', ''),
        national_id_image,
        'pending'
    ))
    
    user_id = cursor.lastrowid
    
    if data['role'] == 'owner':
        chalet_card_image = data.get('chalet_card_image', '')
        if chalet_card_image and not chalet_card_image.startswith('uploads/'):
            chalet_card_image = f"uploads/{chalet_card_image}"
        
        cursor.execute('''
            INSERT INTO owner_details (user_id, chalet_number, chalet_card_image, business_name)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            data.get('chalet_number', ''),
            chalet_card_image,
            data.get('business_name', '')
        ))
    elif data['role'] == 'customer':
        cursor.execute('''
            INSERT INTO customer_details (user_id, date_of_birth, address, emergency_contact)
            VALUES (?, ?, ?, ?)
        ''', (
            user_id,
            data.get('date_of_birth', ''),
            data.get('address', ''),
            data.get('emergency_contact', '')
        ))
    
    conn.commit()
    conn.close()
    return user_id

def update_user(user_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET name = ?, email = ?, phone = ?, national_id = ?
        WHERE id = ?
    ''', (data.get('name'), data.get('email'), data.get('phone'), data.get('national_id'), user_id))
    conn.commit()
    conn.close()

def update_user_role(user_id, new_role):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return False
    
    if user['role'] == 'admin':
        admin_count = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0]
        if admin_count <= 1 and new_role != 'admin':
            conn.close()
            return False
    
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    
    if new_role == 'owner':
        existing = cursor.execute('SELECT * FROM owner_details WHERE user_id = ?', (user_id,)).fetchone()
        if not existing:
            cursor.execute('''
                INSERT INTO owner_details (user_id, chalet_number, business_name)
                VALUES (?, ?, ?)
            ''', (user_id, f'PENDING-{user_id}', 'يحتاج إلى تحديث'))
    
    if user['role'] == 'owner' and new_role != 'owner':
        cursor.execute('DELETE FROM owner_details WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM chalets WHERE owner_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    return True

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        return False
    
    if user['role'] == 'admin':
        admin_count = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0]
        if admin_count <= 1:
            conn.close()
            return False
    
    cursor.execute('DELETE FROM owner_details WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM customer_details WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM chalets WHERE owner_id = ?', (user_id,))
    cursor.execute('DELETE FROM bookings WHERE customer_id = ?', (user_id,))
    cursor.execute('DELETE FROM bookings WHERE chalet_id IN (SELECT id FROM chalets WHERE owner_id = ?)', (user_id,))
    cursor.execute('DELETE FROM payments WHERE customer_id = ?', (user_id,))
    cursor.execute('DELETE FROM testimonials WHERE customer_id = ?', (user_id,))
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

def get_user_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    total_users = cursor.execute('SELECT COUNT(*) FROM users WHERE role != "admin"').fetchone()[0]
    pending_users = cursor.execute('SELECT COUNT(*) FROM users WHERE status = "pending"').fetchone()[0]
    approved_users = cursor.execute('SELECT COUNT(*) FROM users WHERE status = "approved" AND role != "admin"').fetchone()[0]
    rejected_users = cursor.execute('SELECT COUNT(*) FROM users WHERE status = "rejected"').fetchone()[0]
    owners = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "owner" AND status = "approved"').fetchone()[0]
    customers = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "customer" AND status = "approved"').fetchone()[0]
    admins = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"').fetchone()[0]
    conn.close()
    return {'total': total_users, 'pending': pending_users, 'approved': approved_users,
            'rejected': rejected_users, 'owners': owners, 'customers': customers, 'admins': admins}

# --- دوال إدارة التصنيفات ---

def get_categories():
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY id').fetchall()
    conn.close()
    result = []
    for cat in categories:
        cat_dict = dict(cat)
        if 'image' not in cat_dict or not cat_dict['image']:
            cat_dict['image'] = 'default_category.jpg'
        result.append(cat_dict)
    return result

def get_category_by_id(category_id):
    conn = get_db_connection()
    category = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
    conn.close()
    if category:
        cat_dict = dict(category)
        if 'image' not in cat_dict or not cat_dict['image']:
            cat_dict['image'] = 'default_category.jpg'
        return cat_dict
    return None

# --- دوال إدارة صور الشاليهات ---

def add_chalet_image(chalet_id, image_path, is_main=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    if is_main:
        cursor.execute('UPDATE chalet_images SET is_main = 0 WHERE chalet_id = ?', (chalet_id,))
    cursor.execute('''
        INSERT INTO chalet_images (chalet_id, image, is_main)
        VALUES (?, ?, ?)
    ''', (chalet_id, image_path, is_main))
    conn.commit()
    conn.close()
    return cursor.lastrowid

def get_chalet_images(chalet_id):
    conn = get_db_connection()
    images = conn.execute('''
        SELECT * FROM chalet_images WHERE chalet_id = ? ORDER BY is_main DESC, created_at DESC
    ''', (chalet_id,)).fetchall()
    conn.close()
    return [dict(img) for img in images]

def delete_chalet_image(image_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM chalet_images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

def set_main_chalet_image(image_id, chalet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE chalet_images SET is_main = 0 WHERE chalet_id = ?', (chalet_id,))
    cursor.execute('UPDATE chalet_images SET is_main = 1 WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()

# --- دوال إدارة التواريخ المحجوزة من المالك ---

def add_owner_booked_date(chalet_id, date, reason=''):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO owner_booked_dates (chalet_id, date, reason)
            VALUES (?, ?, ?)
        ''', (chalet_id, date, reason))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def delete_owner_booked_date(chalet_id, date):
    conn = get_db_connection()
    conn.execute('DELETE FROM owner_booked_dates WHERE chalet_id = ? AND date = ?', (chalet_id, date))
    conn.commit()
    conn.close()

def get_owner_booked_dates(chalet_id):
    conn = get_db_connection()
    dates = conn.execute('SELECT * FROM owner_booked_dates WHERE chalet_id = ? ORDER BY date', (chalet_id,)).fetchall()
    conn.close()
    return [dict(d) for d in dates]

def get_booking_dates_for_chalet(chalet_id):
    conn = get_db_connection()
    dates = conn.execute('''
        SELECT DISTINCT bd.date FROM booked_dates bd
        JOIN bookings b ON bd.booking_id = b.id
        WHERE bd.chalet_id = ? AND b.status = 'confirmed'
        ORDER BY bd.date
    ''', (chalet_id,)).fetchall()
    conn.close()
    return [d['date'] for d in dates]

# --- دوال إدارة الشاليهات ---

def create_chalet(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    amenities_json = json.dumps(data.get('amenities', []))
    image = data.get('image', 'C1.jpg')
    if image and not image.startswith('uploads/') and not image.startswith('C'):
        image = f"uploads/chalets/{image}"
    
    cursor.execute('''
        INSERT INTO chalets (name_ar, name_en, description_ar, description_en, 
            price_per_night, owner_id, category_id, image, location, 
            bedrooms, bathrooms, max_guests, amenities, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['name_ar'], data['name_en'], data.get('description_ar', ''), data.get('description_en', ''),
        data['price_per_night'], data['owner_id'], data.get('category_id'), image,
        data.get('location', 'العين السخنة، السويس، مصر'),
        data.get('bedrooms', 2), data.get('bathrooms', 2), data.get('max_guests', 6),
        amenities_json, 'pending'
    ))
    chalet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chalet_id

def get_chalets_by_owner(owner_id):
    conn = get_db_connection()
    chalets = conn.execute('''
        SELECT c.*, cat.name_ar as category_name_ar, cat.name_en as category_name_en
        FROM chalets c LEFT JOIN categories cat ON c.category_id = cat.id
        WHERE c.owner_id = ? ORDER BY c.created_at DESC
    ''', (owner_id,)).fetchall()
    conn.close()
    result = []
    for chalet in chalets:
        chalet_dict = dict(chalet)
        chalet_dict['amenities'] = json.loads(chalet_dict['amenities']) if chalet_dict.get('amenities') else ['مسبح', 'واي فاي', 'تكييف']
        result.append(chalet_dict)
    return result

def get_all_chalets():
    conn = get_db_connection()
    chalets = conn.execute('''
        SELECT c.*, u.name as owner_name, u.phone as owner_phone,
               cat.name_ar as category_name_ar, cat.name_en as category_name_en,
               cat.icon as category_icon, cat.image as category_image
        FROM chalets c
        LEFT JOIN users u ON c.owner_id = u.id
        LEFT JOIN categories cat ON c.category_id = cat.id
        WHERE c.status = 'approved'
        ORDER BY c.created_at DESC
    ''').fetchall()
    
    result = []
    for chalet in chalets:
        chalet_dict = dict(chalet)
        chalet_dict['amenities'] = json.loads(chalet_dict['amenities']) if chalet_dict.get('amenities') else ['مسبح', 'واي فاي', 'تكييف']
        images = conn.execute('''
            SELECT * FROM chalet_images WHERE chalet_id = ? ORDER BY is_main DESC, created_at DESC
        ''', (chalet['id'],)).fetchall()
        chalet_dict['images'] = [dict(img) for img in images]
        result.append(chalet_dict)
    
    conn.close()
    return result

def get_pending_chalets():
    conn = get_db_connection()
    chalets = conn.execute('''
        SELECT c.*, u.name as owner_name, u.phone as owner_phone,
               cat.name_ar as category_name_ar, cat.name_en as category_name_en
        FROM chalets c
        LEFT JOIN users u ON c.owner_id = u.id
        LEFT JOIN categories cat ON c.category_id = cat.id
        WHERE c.status = 'pending'
        ORDER BY c.created_at DESC
    ''').fetchall()
    conn.close()
    result = []
    for chalet in chalets:
        chalet_dict = dict(chalet)
        chalet_dict['amenities'] = json.loads(chalet_dict['amenities']) if chalet_dict.get('amenities') else ['مسبح', 'واي فاي', 'تكييف']
        result.append(chalet_dict)
    return result

def approve_chalet(chalet_id, admin_id):
    conn = get_db_connection()
    conn.execute('''
        UPDATE chalets SET status = 'approved', approved_at = CURRENT_TIMESTAMP, approved_by = ?
        WHERE id = ?
    ''', (admin_id, chalet_id))
    conn.commit()
    conn.close()

def reject_chalet(chalet_id):
    conn = get_db_connection()
    conn.execute('UPDATE chalets SET status = "rejected" WHERE id = ?', (chalet_id,))
    conn.commit()
    conn.close()

def get_chalet_by_id(chalet_id):
    conn = get_db_connection()
    chalet = conn.execute('''
        SELECT c.*, u.name as owner_name, u.phone as owner_phone,
               cat.name_ar as category_name_ar, cat.name_en as category_name_en,
               cat.icon as category_icon, cat.image as category_image
        FROM chalets c
        LEFT JOIN users u ON c.owner_id = u.id
        LEFT JOIN categories cat ON c.category_id = cat.id
        WHERE c.id = ?
    ''', (chalet_id,)).fetchone()
    
    if chalet:
        chalet_dict = dict(chalet)
        chalet_dict['amenities'] = json.loads(chalet_dict['amenities']) if chalet_dict.get('amenities') else ['مسبح', 'واي فاي', 'تكييف']
        images = conn.execute('''
            SELECT * FROM chalet_images WHERE chalet_id = ? ORDER BY is_main DESC, created_at DESC
        ''', (chalet_id,)).fetchall()
        chalet_dict['images'] = [dict(img) for img in images]
        conn.close()
        return chalet_dict
    
    conn.close()
    return None

def delete_chalet(chalet_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM chalets WHERE id = ?', (chalet_id,))
    conn.commit()
    conn.close()

# --- دوال إدارة الحجوزات ---

def create_booking(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (chalet_id, customer_id, start_date, end_date, 
            status, payment_method, amount, days)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['chalet_id'], data['customer_id'], data['start_date'], data['end_date'],
        'pending', data.get('payment_method', 'bank_transfer'), data['amount'], data['days']
    ))
    booking_id = cursor.lastrowid
    
    start = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end = datetime.strptime(data['end_date'], '%Y-%m-%d')
    current = start
    while current <= end:
        cursor.execute('''
            INSERT INTO booked_dates (chalet_id, booking_id, date)
            VALUES (?, ?, ?)
        ''', (data['chalet_id'], booking_id, current.strftime('%Y-%m-%d')))
        current += timedelta(days=1)
    
    conn.commit()
    conn.close()
    return booking_id

def get_all_booked_dates(chalet_id):
    conn = get_db_connection()
    booking_dates = conn.execute('''
        SELECT bd.date FROM booked_dates bd
        JOIN bookings b ON bd.booking_id = b.id
        WHERE bd.chalet_id = ? AND b.status = 'confirmed'
        AND bd.date >= date('now')
    ''', (chalet_id,)).fetchall()
    owner_dates = conn.execute('SELECT date FROM owner_booked_dates WHERE chalet_id = ?', (chalet_id,)).fetchall()
    conn.close()
    all_dates = [d['date'] for d in booking_dates] + [d['date'] for d in owner_dates]
    return all_dates

def check_availability_with_owner_dates(chalet_id, start_date, end_date):
    conn = get_db_connection()
    owner_dates = conn.execute('''
        SELECT date FROM owner_booked_dates WHERE chalet_id = ? AND date BETWEEN ? AND ?
    ''', (chalet_id, start_date, end_date)).fetchall()
    booking_dates = conn.execute('''
        SELECT bd.date FROM booked_dates bd
        JOIN bookings b ON bd.booking_id = b.id
        WHERE bd.chalet_id = ? AND b.status = 'confirmed'
        AND bd.date BETWEEN ? AND ?
    ''', (chalet_id, start_date, end_date)).fetchall()
    conn.close()
    all_dates = [d['date'] for d in owner_dates] + [d['date'] for d in booking_dates]
    return len(all_dates) == 0

def get_bookings():
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               u.name as customer_name, u.phone as customer_phone,
               u2.name as owner_name, u2.phone as owner_phone,
               u.national_id as customer_national_id
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON b.customer_id = u.id
        LEFT JOIN users u2 ON c.owner_id = u2.id
        ORDER BY b.created_at DESC
    ''').fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def get_bookings_by_owner(owner_id):
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               u.name as customer_name, u.phone as customer_phone,
               u.national_id as customer_national_id
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON b.customer_id = u.id
        WHERE c.owner_id = ?
        ORDER BY b.created_at DESC
    ''', (owner_id,)).fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def get_bookings_by_customer(customer_id):
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               c.image as chalet_image, u.name as owner_name, u.phone as owner_phone
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE b.customer_id = ?
        ORDER BY b.created_at DESC
    ''', (customer_id,)).fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def update_booking_status(booking_id, status):
    conn = get_db_connection()
    conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    conn.close()

def get_booking_by_id(booking_id):
    conn = get_db_connection()
    booking = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               c.image as chalet_image, c.location as chalet_location,
               c.price_per_night as chalet_price,
               u.name as customer_name, u.phone as customer_phone,
               u.national_id as customer_national_id, u.email as customer_email,
               u2.name as owner_name, u2.phone as owner_phone,
               u2.email as owner_email
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON b.customer_id = u.id
        LEFT JOIN users u2 ON c.owner_id = u2.id
        WHERE b.id = ?
    ''', (booking_id,)).fetchone()
    conn.close()
    return dict(booking) if booking else None

def get_pending_bookings_by_owner(owner_id):
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               u.name as customer_name, u.phone as customer_phone,
               u.national_id as customer_national_id
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON b.customer_id = u.id
        WHERE c.owner_id = ? AND b.status = 'pending'
        ORDER BY b.created_at DESC
    ''', (owner_id,)).fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def get_bookings_by_owner_all(owner_id):
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.name_ar as chalet_name_ar, c.name_en as chalet_name_en,
               u.name as customer_name, u.phone as customer_phone,
               u.national_id as customer_national_id
        FROM bookings b
        LEFT JOIN chalets c ON b.chalet_id = c.id
        LEFT JOIN users u ON b.customer_id = u.id
        WHERE c.owner_id = ?
        ORDER BY b.created_at DESC
    ''', (owner_id,)).fetchall()
    conn.close()
    return [dict(booking) for booking in bookings]

def update_booking_status_by_owner(booking_id, status, owner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    booking = cursor.execute('''
        SELECT b.*, c.owner_id FROM bookings b
        JOIN chalets c ON b.chalet_id = c.id
        WHERE b.id = ? AND c.owner_id = ?
    ''', (booking_id, owner_id)).fetchone()
    
    if not booking:
        conn.close()
        return False
    
    if booking['status'] == 'confirmed' and status == 'cancelled':
        cursor.execute('DELETE FROM booked_dates WHERE booking_id = ?', (booking_id,))
    
    cursor.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    conn.close()
    return True

# --- دوال الإحصائيات ---

def get_statistics():
    conn = get_db_connection()
    total_chalets = conn.execute('SELECT COUNT(*) FROM chalets WHERE status = "approved"').fetchone()[0]
    pending_chalets = conn.execute('SELECT COUNT(*) FROM chalets WHERE status = "pending"').fetchone()[0]
    total_bookings = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
    pending_bookings = conn.execute('SELECT COUNT(*) FROM bookings WHERE status = "pending"').fetchone()[0]
    total_users = conn.execute('SELECT COUNT(*) FROM users WHERE role != "admin"').fetchone()[0]
    pending_users = conn.execute('SELECT COUNT(*) FROM users WHERE status = "pending"').fetchone()[0]
    revenue = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM bookings WHERE status = "confirmed"').fetchone()[0]
    conn.close()
    return {
        'total_chalets': total_chalets,
        'pending_chalets': pending_chalets,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'total_users': total_users,
        'pending_users': pending_users,
        'revenue': revenue
    }

print("✅ تم تحميل قاعدة البيانات بنجاح!")
