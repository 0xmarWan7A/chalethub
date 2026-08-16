# database.py
import os
import json
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# تهيئة Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

# استخدام service role key للتشغيل الكامل
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY or SUPABASE_KEY)

def get_db():
    """الحصول على اتصال Supabase"""
    return supabase

def generate_uuid():
    """توليد UUID جديد"""
    return str(uuid.uuid4())

def init_db():
    """تهيئة قاعدة البيانات"""
    print("✅ استخدام قاعدة بيانات Supabase")
    insert_default_data()

def insert_default_data():
    """إدخال البيانات الافتراضية"""
    try:
        # التحقق من وجود التصنيفات
        categories = supabase.table('categories').select('*').execute()
        if not categories.data:
            default_categories = [
                {'name_ar': 'ميني إيجيبت', 'name_en': 'Mini Egypt', 'description': 'شاليهات فاخرة بتصميم مصري أصيل', 'icon': 'bi-pyramid', 'image': 'mini_egypt.jpg'},
                {'name_ar': 'ريد كاربت', 'name_en': 'Red Carpet', 'description': 'شاليهات فاخرة بأسلوب هوليودي', 'icon': 'bi-star', 'image': 'red_carpet.jpg'},
                {'name_ar': 'نيو ريد كاربت', 'name_en': 'New Red Carpet', 'description': 'شاليهات فاخرة محدثة بأحدث التصاميم', 'icon': 'bi-gem', 'image': 'new_red_carpet.jpg'}
            ]
            for cat in default_categories:
                supabase.table('categories').insert(cat).execute()
            print("✅ تم إضافة التصنيفات الافتراضية")
        
        # التحقق من وجود المستخدمين
        users = supabase.table('users').select('*').eq('role', 'admin').execute()
        if not users.data:
            # مدير النظام
            admin = {
                'id': generate_uuid(),
                'username': 'admin',
                'password': generate_password_hash('admin123'),
                'role': 'admin',
                'name': 'مدير النظام',
                'email': 'admin@lasreina.com',
                'phone': '+20123456789',
                'national_id': '12345678901234',
                'status': 'approved'
            }
            supabase.table('users').insert(admin).execute()
            
            # مالك تجريبي
            owner_id = generate_uuid()
            owner = {
                'id': owner_id,
                'username': 'owner',
                'password': generate_password_hash('owner123'),
                'role': 'owner',
                'name': 'مالك قرية لاسرينا',
                'email': 'owner@lasreina.com',
                'phone': '+20123456789',
                'national_id': '98765432109876',
                'status': 'approved'
            }
            supabase.table('users').insert(owner).execute()
            
            # تفاصيل المالك
            supabase.table('owner_details').insert({
                'id': generate_uuid(),
                'user_id': owner_id,
                'chalet_number': 'LSR-2024-001',
                'business_name': 'قرية لاسرينا'
            }).execute()
            
            # عميل تجريبي
            customer = {
                'id': generate_uuid(),
                'username': 'customer',
                'password': generate_password_hash('customer123'),
                'role': 'customer',
                'name': 'عميل تجريبي',
                'email': 'customer@lasreina.com',
                'phone': '+20123456789',
                'national_id': '12345678901234',
                'status': 'approved'
            }
            supabase.table('users').insert(customer).execute()
            
            print("✅ تم إضافة المستخدمين الافتراضيين")
            
    except Exception as e:
        print(f"⚠️ خطأ في إدخال البيانات: {e}")

# تهيئة قاعدة البيانات
init_db()

# ============================================================
# دوال إدارة المستخدمين
# ============================================================

def get_user_by_id(user_id):
    """الحصول على مستخدم بواسطة المعرف"""
    try:
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user.data:
            return None
        
        user_data = user.data[0]
        
        if user_data.get('role') == 'owner':
            owner = supabase.table('owner_details').select('*').eq('user_id', user_id).execute()
            if owner.data:
                user_data.update(owner.data[0])
        
        if user_data.get('role') == 'customer':
            customer = supabase.table('customer_details').select('*').eq('user_id', user_id).execute()
            if customer.data:
                user_data.update(customer.data[0])
        
        return user_data
    except Exception as e:
        print(f"خطأ في get_user_by_id: {e}")
        return None

def get_user_by_username(username):
    """الحصول على مستخدم بواسطة اسم المستخدم"""
    try:
        user = supabase.table('users').select('*').eq('username', username).execute()
        return user.data[0] if user.data else None
    except Exception as e:
        print(f"خطأ في get_user_by_username: {e}")
        return None

def get_all_users():
    """الحصول على جميع المستخدمين"""
    try:
        users = supabase.table('users').select('*').order('created_at', desc=True).execute()
        
        result = []
        for user in users.data if users.data else []:
            if user.get('role') == 'owner':
                owner = supabase.table('owner_details').select('*').eq('user_id', user['id']).execute()
                if owner.data:
                    user.update(owner.data[0])
            elif user.get('role') == 'customer':
                customer = supabase.table('customer_details').select('*').eq('user_id', user['id']).execute()
                if customer.data:
                    user.update(customer.data[0])
            
            if user.get('role') == 'owner':
                chalets = supabase.table('chalets').select('*', count='exact').eq('owner_id', user['id']).execute()
                user['chalet_count'] = chalets.count
            
            result.append(user)
        
        return result
    except Exception as e:
        print(f"خطأ في get_all_users: {e}")
        return []

def get_pending_users():
    """الحصول على المستخدمين المعلقين"""
    try:
        users = supabase.table('users').select('*').eq('status', 'pending').neq('role', 'admin').order('created_at', desc=True).execute()
        
        result = []
        for user in users.data if users.data else []:
            if user.get('role') == 'owner':
                owner = supabase.table('owner_details').select('*').eq('user_id', user['id']).execute()
                if owner.data:
                    user.update(owner.data[0])
            result.append(user)
        
        return result
    except Exception as e:
        print(f"خطأ في get_pending_users: {e}")
        return []

def approve_user(user_id, admin_id):
    """الموافقة على مستخدم"""
    try:
        supabase.table('users').update({
            'status': 'approved',
            'approved_at': datetime.now().isoformat(),
            'approved_by': admin_id
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في approve_user: {e}")
        return False

def reject_user(user_id):
    """رفض مستخدم"""
    try:
        supabase.table('users').update({'status': 'rejected'}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في reject_user: {e}")
        return False

def create_user(data):
    """إنشاء مستخدم جديد"""
    try:
        if not data.get('username') or not data.get('password'):
            print("❌ اسم المستخدم أو كلمة المرور مفقودة")
            return None
        
        user_id = generate_uuid()
        
        hashed_password = generate_password_hash(data['password'])
        
        user_data = {
            'id': user_id,
            'username': data['username'],
            'password': hashed_password,
            'role': data.get('role', 'customer'),
            'name': data.get('name', ''),
            'email': data.get('email', ''),
            'phone': data.get('phone', ''),
            'national_id': data.get('national_id', ''),
            'national_id_image': data.get('national_id_image', ''),
            'status': 'pending'
        }
        
        result = supabase.table('users').insert(user_data).execute()
        
        if not result.data:
            print("❌ فشل إنشاء المستخدم")
            return None
        
        user_id = result.data[0]['id']
        
        if data.get('role') == 'owner':
            owner_data = {
                'id': generate_uuid(),
                'user_id': user_id,
                'chalet_number': data.get('chalet_number', ''),
                'chalet_card_image': data.get('chalet_card_image', ''),
                'business_name': data.get('business_name', '')
            }
            supabase.table('owner_details').insert(owner_data).execute()
            
        elif data.get('role') == 'customer':
            customer_data = {
                'id': generate_uuid(),
                'user_id': user_id,
                'date_of_birth': data.get('date_of_birth', ''),
                'address': data.get('address', ''),
                'emergency_contact': data.get('emergency_contact', '')
            }
            supabase.table('customer_details').insert(customer_data).execute()
        
        return user_id
        
    except Exception as e:
        print(f"❌ خطأ في create_user: {str(e)}")
        return None

def update_user(user_id, data):
    """تحديث بيانات المستخدم"""
    try:
        supabase.table('users').update({
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'national_id': data.get('national_id')
        }).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في update_user: {e}")
        return False

def update_user_role(user_id, new_role):
    """تحديث دور المستخدم"""
    try:
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user.data:
            return False
        
        if user.data[0]['role'] == 'admin':
            admins = supabase.table('users').select('*').eq('role', 'admin').execute()
            if len(admins.data) <= 1 and new_role != 'admin':
                return False
        
        supabase.table('users').update({'role': new_role}).eq('id', user_id).execute()
        
        if new_role == 'owner':
            details = supabase.table('owner_details').select('*').eq('user_id', user_id).execute()
            if not details.data:
                supabase.table('owner_details').insert({
                    'id': generate_uuid(),
                    'user_id': user_id,
                    'chalet_number': f'PENDING-{user_id[:8]}',
                    'business_name': 'يحتاج إلى تحديث'
                }).execute()
        
        if user.data[0]['role'] == 'owner' and new_role != 'owner':
            supabase.table('owner_details').delete().eq('user_id', user_id).execute()
            supabase.table('chalets').delete().eq('owner_id', user_id).execute()
        
        return True
    except Exception as e:
        print(f"خطأ في update_user_role: {e}")
        return False

def delete_user(user_id):
    """حذف مستخدم وجميع بياناته"""
    try:
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        if not user.data:
            return False
        
        if user.data[0]['role'] == 'admin':
            admins = supabase.table('users').select('*').eq('role', 'admin').execute()
            if len(admins.data) <= 1:
                return False
        
        supabase.table('owner_details').delete().eq('user_id', user_id).execute()
        supabase.table('customer_details').delete().eq('user_id', user_id).execute()
        supabase.table('chalets').delete().eq('owner_id', user_id).execute()
        supabase.table('bookings').delete().eq('customer_id', user_id).execute()
        supabase.table('payments').delete().eq('customer_id', user_id).execute()
        supabase.table('testimonials').delete().eq('customer_id', user_id).execute()
        supabase.table('users').delete().eq('id', user_id).execute()
        
        return True
    except Exception as e:
        print(f"خطأ في delete_user: {e}")
        return False

def get_user_statistics():
    """الحصول على إحصائيات المستخدمين"""
    try:
        total = supabase.table('users').select('*', count='exact').neq('role', 'admin').execute()
        pending = supabase.table('users').select('*', count='exact').eq('status', 'pending').execute()
        approved = supabase.table('users').select('*', count='exact').eq('status', 'approved').neq('role', 'admin').execute()
        rejected = supabase.table('users').select('*', count='exact').eq('status', 'rejected').execute()
        owners = supabase.table('users').select('*', count='exact').eq('role', 'owner').eq('status', 'approved').execute()
        customers = supabase.table('users').select('*', count='exact').eq('role', 'customer').eq('status', 'approved').execute()
        admins = supabase.table('users').select('*', count='exact').eq('role', 'admin').execute()
        
        return {
            'total': total.count,
            'pending': pending.count,
            'approved': approved.count,
            'rejected': rejected.count,
            'owners': owners.count,
            'customers': customers.count,
            'admins': admins.count
        }
    except Exception as e:
        print(f"خطأ في get_user_statistics: {e}")
        return {'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0, 'owners': 0, 'customers': 0, 'admins': 0}

# ============================================================
# دوال إدارة التصنيفات
# ============================================================

def get_categories():
    """الحصول على جميع التصنيفات"""
    try:
        categories = supabase.table('categories').select('*').order('created_at').execute()
        return categories.data if categories.data else []
    except Exception as e:
        print(f"خطأ في get_categories: {e}")
        return []

def get_category_by_id(category_id):
    """الحصول على تصنيف بواسطة المعرف"""
    try:
        category = supabase.table('categories').select('*').eq('id', category_id).execute()
        return category.data[0] if category.data else None
    except Exception as e:
        print(f"خطأ في get_category_by_id: {e}")
        return None

# ============================================================
# دوال إدارة صور الشاليهات
# ============================================================

def add_chalet_image(chalet_id, image_path, is_main=False):
    """إضافة صورة للشاليه"""
    try:
        if is_main:
            supabase.table('chalet_images').update({'is_main': False}).eq('chalet_id', chalet_id).execute()
        
        result = supabase.table('chalet_images').insert({
            'id': generate_uuid(),
            'chalet_id': chalet_id,
            'image': image_path,
            'is_main': is_main
        }).execute()
        return result.data[0]['id'] if result.data else None
    except Exception as e:
        print(f"خطأ في add_chalet_image: {e}")
        return None

def get_chalet_images(chalet_id):
    """الحصول على جميع صور الشاليه"""
    try:
        images = supabase.table('chalet_images').select('*').eq('chalet_id', chalet_id).order('is_main', desc=True).order('created_at', desc=True).execute()
        return images.data if images.data else []
    except Exception as e:
        print(f"خطأ في get_chalet_images: {e}")
        return []

def delete_chalet_image(image_id):
    """حذف صورة شاليه"""
    try:
        supabase.table('chalet_images').delete().eq('id', image_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في delete_chalet_image: {e}")
        return False

def set_main_chalet_image(image_id, chalet_id):
    """تعيين صورة رئيسية للشاليه"""
    try:
        supabase.table('chalet_images').update({'is_main': False}).eq('chalet_id', chalet_id).execute()
        supabase.table('chalet_images').update({'is_main': True}).eq('id', image_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في set_main_chalet_image: {e}")
        return False

def get_chalet_image_by_id(image_id):
    """الحصول على صورة شاليه بواسطة المعرف"""
    try:
        image = supabase.table('chalet_images').select('*').eq('id', image_id).execute()
        return image.data[0] if image.data else None
    except Exception as e:
        print(f"خطأ في get_chalet_image_by_id: {e}")
        return None

# ============================================================
# دوال إدارة التواريخ المحجوزة من المالك
# ============================================================

def add_owner_booked_date(chalet_id, date, reason=''):
    """إضافة تاريخ محجوز من قبل المالك"""
    try:
        supabase.table('owner_booked_dates').insert({
            'id': generate_uuid(),
            'chalet_id': chalet_id,
            'date': date,
            'reason': reason
        }).execute()
        return True
    except Exception as e:
        print(f"خطأ في add_owner_booked_date: {e}")
        return False

def delete_owner_booked_date(chalet_id, date):
    """حذف تاريخ محجوز من قبل المالك"""
    try:
        supabase.table('owner_booked_dates').delete().eq('chalet_id', chalet_id).eq('date', date).execute()
        return True
    except Exception as e:
        print(f"خطأ في delete_owner_booked_date: {e}")
        return False

def get_owner_booked_dates(chalet_id):
    """الحصول على التواريخ المحجوزة من قبل المالك"""
    try:
        dates = supabase.table('owner_booked_dates').select('*').eq('chalet_id', chalet_id).order('date').execute()
        return dates.data if dates.data else []
    except Exception as e:
        print(f"خطأ في get_owner_booked_dates: {e}")
        return []

def get_booking_dates_for_chalet(chalet_id):
    """الحصول على التواريخ المحجوزة من الحجوزات المؤكدة"""
    try:
        confirmed_bookings = supabase.table('bookings').select('id').eq('chalet_id', chalet_id).eq('status', 'confirmed').execute()
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        if not booking_ids:
            return []
        
        dates = supabase.table('booked_dates').select('date').eq('chalet_id', chalet_id).in_('booking_id', booking_ids).execute()
        return [d['date'] for d in dates.data] if dates.data else []
    except Exception as e:
        print(f"خطأ في get_booking_dates_for_chalet: {e}")
        return []

# ============================================================
# دوال إدارة الشاليهات
# ============================================================

def create_chalet(data):
    """إنشاء شاليه جديد"""
    try:
        chalet_id = generate_uuid()
        chalet_data = {
            'id': chalet_id,
            'name_ar': data['name_ar'],
            'name_en': data.get('name_en', data['name_ar']),
            'description_ar': data.get('description_ar', ''),
            'description_en': data.get('description_en', ''),
            'price_per_night': data['price_per_night'],
            'owner_id': data['owner_id'],
            'category_id': data.get('category_id'),
            'image': data.get('image', 'C1.jpg'),
            'location': data.get('location', 'العين السخنة، السويس، مصر'),
            'bedrooms': data.get('bedrooms', 2),
            'bathrooms': data.get('bathrooms', 2),
            'max_guests': data.get('max_guests', 6),
            'amenities': json.dumps(data.get('amenities', [])),
            'status': 'pending'
        }
        
        result = supabase.table('chalets').insert(chalet_data).execute()
        return result.data[0]['id'] if result.data else None
    except Exception as e:
        print(f"خطأ في create_chalet: {e}")
        return None

def get_chalets_by_owner(owner_id):
    """الحصول على شاليهات المالك"""
    try:
        chalets = supabase.table('chalets').select('*').eq('owner_id', owner_id).order('created_at', desc=True).execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
            if chalet.get('category_id'):
                category = supabase.table('categories').select('name_ar, name_en').eq('id', chalet['category_id']).execute()
                if category.data:
                    chalet['category_name_ar'] = category.data[0]['name_ar']
                    chalet['category_name_en'] = category.data[0]['name_en']
            
            if chalet.get('amenities'):
                chalet['amenities'] = json.loads(chalet['amenities'])
            else:
                chalet['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
            result.append(chalet)
        return result
    except Exception as e:
        print(f"خطأ في get_chalets_by_owner: {e}")
        return []

def get_all_chalets():
    """الحصول على جميع الشاليهات الموافق عليها"""
    try:
        chalets = supabase.table('chalets').select('*').eq('status', 'approved').order('created_at', desc=True).execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
            owner = supabase.table('users').select('name, phone').eq('id', chalet['owner_id']).execute()
            if owner.data:
                chalet['owner_name'] = owner.data[0]['name']
                chalet['owner_phone'] = owner.data[0]['phone']
            
            if chalet.get('category_id'):
                category = supabase.table('categories').select('*').eq('id', chalet['category_id']).execute()
                if category.data:
                    chalet['category_name_ar'] = category.data[0]['name_ar']
                    chalet['category_name_en'] = category.data[0]['name_en']
                    chalet['category_icon'] = category.data[0]['icon']
                    chalet['category_image'] = category.data[0]['image']
            
            images = supabase.table('chalet_images').select('*').eq('chalet_id', chalet['id']).order('is_main', desc=True).order('created_at', desc=True).execute()
            chalet['images'] = images.data if images.data else []
            
            if chalet.get('amenities'):
                chalet['amenities'] = json.loads(chalet['amenities'])
            else:
                chalet['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
            
            result.append(chalet)
        return result
    except Exception as e:
        print(f"خطأ في get_all_chalets: {e}")
        return []

def get_pending_chalets():
    """الحصول على الشاليهات المعلقة"""
    try:
        chalets = supabase.table('chalets').select('*').eq('status', 'pending').order('created_at', desc=True).execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
            owner = supabase.table('users').select('name, phone').eq('id', chalet['owner_id']).execute()
            if owner.data:
                chalet['owner_name'] = owner.data[0]['name']
                chalet['owner_phone'] = owner.data[0]['phone']
            
            if chalet.get('category_id'):
                category = supabase.table('categories').select('name_ar, name_en').eq('id', chalet['category_id']).execute()
                if category.data:
                    chalet['category_name_ar'] = category.data[0]['name_ar']
                    chalet['category_name_en'] = category.data[0]['name_en']
            
            if chalet.get('amenities'):
                chalet['amenities'] = json.loads(chalet['amenities'])
            else:
                chalet['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
            result.append(chalet)
        return result
    except Exception as e:
        print(f"خطأ في get_pending_chalets: {e}")
        return []

def approve_chalet(chalet_id, admin_id):
    """الموافقة على شاليه"""
    try:
        supabase.table('chalets').update({
            'status': 'approved',
            'approved_at': datetime.now().isoformat(),
            'approved_by': admin_id
        }).eq('id', chalet_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في approve_chalet: {e}")
        return False

def reject_chalet(chalet_id):
    """رفض شاليه"""
    try:
        supabase.table('chalets').update({'status': 'rejected'}).eq('id', chalet_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في reject_chalet: {e}")
        return False

def get_chalet_by_id(chalet_id):
    """الحصول على شاليه بواسطة المعرف"""
    try:
        chalet = supabase.table('chalets').select('*').eq('id', chalet_id).execute()
        if not chalet.data:
            return None
        
        chalet_dict = chalet.data[0]
        
        owner = supabase.table('users').select('name, phone').eq('id', chalet_dict['owner_id']).execute()
        if owner.data:
            chalet_dict['owner_name'] = owner.data[0]['name']
            chalet_dict['owner_phone'] = owner.data[0]['phone']
        
        if chalet_dict.get('category_id'):
            category = supabase.table('categories').select('*').eq('id', chalet_dict['category_id']).execute()
            if category.data:
                chalet_dict['category_name_ar'] = category.data[0]['name_ar']
                chalet_dict['category_name_en'] = category.data[0]['name_en']
                chalet_dict['category_icon'] = category.data[0]['icon']
                chalet_dict['category_image'] = category.data[0]['image']
        
        images = supabase.table('chalet_images').select('*').eq('chalet_id', chalet_id).order('is_main', desc=True).order('created_at', desc=True).execute()
        chalet_dict['images'] = images.data if images.data else []
        
        if chalet_dict.get('amenities'):
            chalet_dict['amenities'] = json.loads(chalet_dict['amenities'])
        else:
            chalet_dict['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
        
        return chalet_dict
    except Exception as e:
        print(f"خطأ في get_chalet_by_id: {e}")
        return None

def delete_chalet(chalet_id):
    """حذف شاليه"""
    try:
        supabase.table('chalet_images').delete().eq('chalet_id', chalet_id).execute()
        supabase.table('chalets').delete().eq('id', chalet_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في delete_chalet: {e}")
        return False

# ============================================================
# دوال إدارة الحجوزات
# ============================================================

def create_booking(data):
    """إنشاء حجز جديد"""
    try:
        booking_id = generate_uuid()
        booking_data = {
            'id': booking_id,
            'chalet_id': data['chalet_id'],
            'customer_id': data['customer_id'],
            'start_date': data['start_date'],
            'end_date': data['end_date'],
            'status': 'pending',
            'payment_method': data.get('payment_method', 'bank_transfer'),
            'amount': data['amount'],
            'days': data['days']
        }
        
        result = supabase.table('bookings').insert(booking_data).execute()
        
        start = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end = datetime.strptime(data['end_date'], '%Y-%m-%d')
        current = start
        while current <= end:
            supabase.table('booked_dates').insert({
                'id': generate_uuid(),
                'chalet_id': data['chalet_id'],
                'booking_id': booking_id,
                'date': current.strftime('%Y-%m-%d')
            }).execute()
            current += timedelta(days=1)
        
        return booking_id
    except Exception as e:
        print(f"خطأ في create_booking: {e}")
        return None

def get_all_booked_dates(chalet_id):
    """الحصول على جميع التواريخ المحجوزة"""
    try:
        confirmed_bookings = supabase.table('bookings').select('id').eq('chalet_id', chalet_id).eq('status', 'confirmed').execute()
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        booking_dates = []
        if booking_ids:
            dates = supabase.table('booked_dates').select('date').eq('chalet_id', chalet_id).in_('booking_id', booking_ids).gte('date', datetime.now().strftime('%Y-%m-%d')).execute()
            booking_dates = [d['date'] for d in dates.data] if dates.data else []
        
        owner_dates = supabase.table('owner_booked_dates').select('date').eq('chalet_id', chalet_id).execute()
        owner_dates_list = [d['date'] for d in owner_dates.data] if owner_dates.data else []
        
        all_dates = booking_dates + owner_dates_list
        return all_dates
    except Exception as e:
        print(f"خطأ في get_all_booked_dates: {e}")
        return []

def check_availability_with_owner_dates(chalet_id, start_date, end_date):
    """التحقق من التوفر مع تواريخ المالك"""
    try:
        owner_dates = supabase.table('owner_booked_dates').select('date').eq('chalet_id', chalet_id).gte('date', start_date).lte('date', end_date).execute()
        if owner_dates.data:
            return False
        
        confirmed_bookings = supabase.table('bookings').select('id').eq('chalet_id', chalet_id).eq('status', 'confirmed').execute()
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        if booking_ids:
            booked_dates = supabase.table('booked_dates').select('date').eq('chalet_id', chalet_id).gte('date', start_date).lte('date', end_date).in_('booking_id', booking_ids).execute()
            if booked_dates.data:
                return False
        
        return True
    except Exception as e:
        print(f"خطأ في check_availability_with_owner_dates: {e}")
        return False

def get_bookings():
    """الحصول على جميع الحجوزات"""
    try:
        bookings = supabase.table('bookings').select('*').order('created_at', desc=True).execute()
        
        result = []
        for booking in bookings.data if bookings.data else []:
            chalet = supabase.table('chalets').select('name_ar, name_en').eq('id', booking['chalet_id']).execute()
            if chalet.data:
                booking['chalet_name_ar'] = chalet.data[0]['name_ar']
                booking['chalet_name_en'] = chalet.data[0]['name_en']
            
            customer = supabase.table('users').select('name, phone, national_id').eq('id', booking['customer_id']).execute()
            if customer.data:
                booking['customer_name'] = customer.data[0]['name']
                booking['customer_phone'] = customer.data[0]['phone']
                booking['customer_national_id'] = customer.data[0]['national_id']
            
            if chalet.data:
                owner = supabase.table('users').select('name, phone').eq('id', chalet.data[0]['owner_id']).execute()
                if owner.data:
                    booking['owner_name'] = owner.data[0]['name']
                    booking['owner_phone'] = owner.data[0]['phone']
            
            result.append(booking)
        return result
    except Exception as e:
        print(f"خطأ في get_bookings: {e}")
        return []

def get_bookings_by_owner(owner_id):
    """الحصول على حجوزات شاليهات المالك"""
    try:
        chalets = supabase.table('chalets').select('id').eq('owner_id', owner_id).execute()
        chalet_ids = [c['id'] for c in chalets.data] if chalets.data else []
        
        if not chalet_ids:
            return []
        
        bookings = supabase.table('bookings').select('*').in_('chalet_id', chalet_ids).order('created_at', desc=True).execute()
        
        result = []
        for booking in bookings.data if bookings.data else []:
            chalet = supabase.table('chalets').select('name_ar, name_en').eq('id', booking['chalet_id']).execute()
            if chalet.data:
                booking['chalet_name_ar'] = chalet.data[0]['name_ar']
                booking['chalet_name_en'] = chalet.data[0]['name_en']
            
            customer = supabase.table('users').select('name, phone, national_id').eq('id', booking['customer_id']).execute()
            if customer.data:
                booking['customer_name'] = customer.data[0]['name']
                booking['customer_phone'] = customer.data[0]['phone']
                booking['customer_national_id'] = customer.data[0]['national_id']
            
            result.append(booking)
        return result
    except Exception as e:
        print(f"خطأ في get_bookings_by_owner: {e}")
        return []

def get_bookings_by_customer(customer_id):
    """الحصول على حجوزات العميل"""
    try:
        bookings = supabase.table('bookings').select('*').eq('customer_id', customer_id).order('created_at', desc=True).execute()
        
        result = []
        for booking in bookings.data if bookings.data else []:
            chalet = supabase.table('chalets').select('name_ar, name_en, image').eq('id', booking['chalet_id']).execute()
            if chalet.data:
                booking['chalet_name_ar'] = chalet.data[0]['name_ar']
                booking['chalet_name_en'] = chalet.data[0]['name_en']
                booking['chalet_image'] = chalet.data[0]['image']
                
                owner = supabase.table('users').select('name, phone').eq('id', chalet.data[0]['owner_id']).execute()
                if owner.data:
                    booking['owner_name'] = owner.data[0]['name']
                    booking['owner_phone'] = owner.data[0]['phone']
            
            result.append(booking)
        return result
    except Exception as e:
        print(f"خطأ في get_bookings_by_customer: {e}")
        return []

def update_booking_status(booking_id, status):
    """تحديث حالة الحجز"""
    try:
        supabase.table('bookings').update({'status': status}).eq('id', booking_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في update_booking_status: {e}")
        return False

def get_booking_by_id(booking_id):
    """الحصول على حجز بواسطة المعرف"""
    try:
        booking = supabase.table('bookings').select('*').eq('id', booking_id).execute()
        if not booking.data:
            return None
        
        result = booking.data[0]
        
        chalet = supabase.table('chalets').select('*').eq('id', result['chalet_id']).execute()
        if chalet.data:
            result['chalet'] = chalet.data[0]
        
        customer = supabase.table('users').select('*').eq('id', result['customer_id']).execute()
        if customer.data:
            result['customer'] = customer.data[0]
        
        if chalet.data:
            owner = supabase.table('users').select('*').eq('id', chalet.data[0]['owner_id']).execute()
            if owner.data:
                result['owner'] = owner.data[0]
        
        return result
    except Exception as e:
        print(f"خطأ في get_booking_by_id: {e}")
        return None

def get_pending_bookings_by_owner(owner_id):
    """الحصول على الحجوزات المعلقة لشاليهات المالك"""
    try:
        chalets = supabase.table('chalets').select('id').eq('owner_id', owner_id).execute()
        chalet_ids = [c['id'] for c in chalets.data] if chalets.data else []
        
        if not chalet_ids:
            return []
        
        bookings = supabase.table('bookings').select('*').in_('chalet_id', chalet_ids).eq('status', 'pending').order('created_at', desc=True).execute()
        
        result = []
        for booking in bookings.data if bookings.data else []:
            chalet = supabase.table('chalets').select('name_ar, name_en').eq('id', booking['chalet_id']).execute()
            if chalet.data:
                booking['chalet_name_ar'] = chalet.data[0]['name_ar']
                booking['chalet_name_en'] = chalet.data[0]['name_en']
            
            customer = supabase.table('users').select('name, phone, national_id').eq('id', booking['customer_id']).execute()
            if customer.data:
                booking['customer_name'] = customer.data[0]['name']
                booking['customer_phone'] = customer.data[0]['phone']
                booking['customer_national_id'] = customer.data[0]['national_id']
            
            result.append(booking)
        return result
    except Exception as e:
        print(f"خطأ في get_pending_bookings_by_owner: {e}")
        return []

def get_bookings_by_owner_all(owner_id):
    """الحصول على جميع حجوزات شاليهات المالك"""
    return get_bookings_by_owner(owner_id)

def update_booking_status_by_owner(booking_id, status, owner_id):
    """تحديث حالة الحجز من قبل المالك مع التحقق من الملكية"""
    try:
        booking = supabase.table('bookings').select('*, chalets(owner_id)').eq('id', booking_id).execute()
        
        if not booking.data or booking.data[0]['chalets']['owner_id'] != owner_id:
            return False
        
        if booking.data[0]['status'] == 'confirmed' and status == 'cancelled':
            supabase.table('booked_dates').delete().eq('booking_id', booking_id).execute()
        
        supabase.table('bookings').update({'status': status}).eq('id', booking_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في update_booking_status_by_owner: {e}")
        return False

# ============================================================
# دوال الإحصائيات
# ============================================================

def get_statistics():
    """الحصول على الإحصائيات"""
    try:
        total_chalets = supabase.table('chalets').select('*', count='exact').eq('status', 'approved').execute()
        pending_chalets = supabase.table('chalets').select('*', count='exact').eq('status', 'pending').execute()
        total_bookings = supabase.table('bookings').select('*', count='exact').execute()
        pending_bookings = supabase.table('bookings').select('*', count='exact').eq('status', 'pending').execute()
        total_users = supabase.table('users').select('*', count='exact').neq('role', 'admin').execute()
        pending_users = supabase.table('users').select('*', count='exact').eq('status', 'pending').execute()
        
        revenue_data = supabase.table('bookings').select('amount').eq('status', 'confirmed').execute()
        revenue = sum([b['amount'] for b in revenue_data.data]) if revenue_data.data else 0
        
        return {
            'total_chalets': total_chalets.count,
            'pending_chalets': pending_chalets.count,
            'total_bookings': total_bookings.count,
            'pending_bookings': pending_bookings.count,
            'total_users': total_users.count,
            'pending_users': pending_users.count,
            'revenue': revenue
        }
    except Exception as e:
        print(f"خطأ في get_statistics: {e}")
        return {
            'total_chalets': 0,
            'pending_chalets': 0,
            'total_bookings': 0,
            'pending_bookings': 0,
            'total_users': 0,
            'pending_users': 0,
            'revenue': 0
        }

print("✅ تم تحميل قاعدة البيانات Supabase بنجاح!")
