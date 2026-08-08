# database.py
import os
import json
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
            owner = {
                'username': 'owner',
                'password': generate_password_hash('owner123'),
                'role': 'owner',
                'name': 'مالك قرية لاسرينا',
                'email': 'owner@lasreina.com',
                'phone': '+20123456789',
                'national_id': '98765432109876',
                'status': 'approved'
            }
            owner_result = supabase.table('users').insert(owner).execute()
            owner_id = owner_result.data[0]['id']
            
            # تفاصيل المالك
            supabase.table('owner_details').insert({
                'user_id': owner_id,
                'chalet_number': 'LSR-2024-001',
                'business_name': 'قرية لاسرينا'
            }).execute()
            
            # عميل تجريبي
            customer = {
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

# --- دوال إدارة المستخدمين ---

def get_user_by_id(user_id):
    """الحصول على مستخدم بواسطة المعرف"""
    try:
        user = supabase.table('users').select('*, owner_details(*), customer_details(*)').eq('id', user_id).execute()
        return user.data[0] if user.data else None
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
        users = supabase.table('users')\
            .select('*, owner_details(chalet_number, business_name, chalet_card_image), customer_details(date_of_birth, address)')\
            .order('created_at', desc=True)\
            .execute()
        return users.data if users.data else []
    except Exception as e:
        print(f"خطأ في get_all_users: {e}")
        return []

def get_pending_users():
    """الحصول على المستخدمين المعلقين"""
    try:
        users = supabase.table('users')\
            .select('*, owner_details(*)')\
            .eq('status', 'pending')\
            .neq('role', 'admin')\
            .order('created_at', desc=True)\
            .execute()
        return users.data if users.data else []
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
        user_data = {
            'username': data['username'],
            'password': generate_password_hash(data['password']),
            'role': data['role'],
            'name': data['name'],
            'email': data.get('email', ''),
            'phone': data['phone'],
            'national_id': data.get('national_id', ''),
            'national_id_image': data.get('national_id_image', ''),
            'status': 'pending'
        }
        
        result = supabase.table('users').insert(user_data).execute()
        user_id = result.data[0]['id']
        
        if data['role'] == 'owner':
            supabase.table('owner_details').insert({
                'user_id': user_id,
                'chalet_number': data.get('chalet_number', ''),
                'chalet_card_image': data.get('chalet_card_image', ''),
                'business_name': data.get('business_name', '')
            }).execute()
        elif data['role'] == 'customer':
            supabase.table('customer_details').insert({
                'user_id': user_id,
                'date_of_birth': data.get('date_of_birth', ''),
                'address': data.get('address', ''),
                'emergency_contact': data.get('emergency_contact', '')
            }).execute()
        
        return user_id
    except Exception as e:
        print(f"خطأ في create_user: {e}")
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
                    'user_id': user_id,
                    'chalet_number': f'PENDING-{user_id}',
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

# --- دوال إدارة التصنيفات ---

def get_categories():
    """الحصول على جميع التصنيفات"""
    try:
        categories = supabase.table('categories').select('*').order('id').execute()
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

# --- دوال إدارة صور الشاليهات ---

def add_chalet_image(chalet_id, image_path, is_main=False):
    """إضافة صورة للشاليه"""
    try:
        if is_main:
            supabase.table('chalet_images').update({'is_main': False}).eq('chalet_id', chalet_id).execute()
        
        result = supabase.table('chalet_images').insert({
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
        images = supabase.table('chalet_images')\
            .select('*')\
            .eq('chalet_id', chalet_id)\
            .order('is_main', desc=True)\
            .order('created_at', desc=True)\
            .execute()
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

# --- دوال إدارة التواريخ المحجوزة من المالك ---

def add_owner_booked_date(chalet_id, date, reason=''):
    """إضافة تاريخ محجوز من قبل المالك"""
    try:
        supabase.table('owner_booked_dates').insert({
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
        # الحصول على الحجوزات المؤكدة
        confirmed_bookings = supabase.table('bookings')\
            .select('id')\
            .eq('chalet_id', chalet_id)\
            .eq('status', 'confirmed')\
            .execute()
        
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        if not booking_ids:
            return []
        
        # الحصول على التواريخ المحجوزة
        dates = supabase.table('booked_dates')\
            .select('date')\
            .eq('chalet_id', chalet_id)\
            .in_('booking_id', booking_ids)\
            .execute()
        
        return [d['date'] for d in dates.data] if dates.data else []
    except Exception as e:
        print(f"خطأ في get_booking_dates_for_chalet: {e}")
        return []

# --- دوال إدارة الشاليهات ---

def create_chalet(data):
    """إنشاء شاليه جديد"""
    try:
        chalet_data = {
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
        chalets = supabase.table('chalets')\
            .select('*, categories(name_ar as category_name_ar, name_en as category_name_en)')\
            .eq('owner_id', owner_id)\
            .order('created_at', desc=True)\
            .execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
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
        chalets = supabase.table('chalets')\
            .select('*, users!chalets_owner_id_fkey(name as owner_name, phone as owner_phone), categories(name_ar as category_name_ar, name_en as category_name_en, icon as category_icon, image as category_image)')\
            .eq('status', 'approved')\
            .order('created_at', desc=True)\
            .execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
            if chalet.get('amenities'):
                chalet['amenities'] = json.loads(chalet['amenities'])
            else:
                chalet['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
            
            # الحصول على الصور
            images = supabase.table('chalet_images')\
                .select('*')\
                .eq('chalet_id', chalet['id'])\
                .order('is_main', desc=True)\
                .order('created_at', desc=True)\
                .execute()
            chalet['images'] = images.data if images.data else []
            result.append(chalet)
        return result
    except Exception as e:
        print(f"خطأ في get_all_chalets: {e}")
        return []

def get_pending_chalets():
    """الحصول على الشاليهات المعلقة"""
    try:
        chalets = supabase.table('chalets')\
            .select('*, users!chalets_owner_id_fkey(name as owner_name, phone as owner_phone), categories(name_ar as category_name_ar, name_en as category_name_en)')\
            .eq('status', 'pending')\
            .order('created_at', desc=True)\
            .execute()
        
        result = []
        for chalet in chalets.data if chalets.data else []:
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
        chalet = supabase.table('chalets')\
            .select('*, users!chalets_owner_id_fkey(name as owner_name, phone as owner_phone), categories(name_ar as category_name_ar, name_en as category_name_en, icon as category_icon, image as category_image)')\
            .eq('id', chalet_id)\
            .execute()
        
        if not chalet.data:
            return None
        
        chalet_dict = chalet.data[0]
        if chalet_dict.get('amenities'):
            chalet_dict['amenities'] = json.loads(chalet_dict['amenities'])
        else:
            chalet_dict['amenities'] = ['مسبح', 'واي فاي', 'تكييف']
        
        images = supabase.table('chalet_images')\
            .select('*')\
            .eq('chalet_id', chalet_id)\
            .order('is_main', desc=True)\
            .order('created_at', desc=True)\
            .execute()
        chalet_dict['images'] = images.data if images.data else []
        
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

# --- دوال إدارة الحجوزات ---

def create_booking(data):
    """إنشاء حجز جديد"""
    try:
        booking_data = {
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
        booking_id = result.data[0]['id']
        
        # إضافة التواريخ المحجوزة
        start = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end = datetime.strptime(data['end_date'], '%Y-%m-%d')
        current = start
        while current <= end:
            supabase.table('booked_dates').insert({
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
        # الحصول على الحجوزات المؤكدة
        confirmed_bookings = supabase.table('bookings')\
            .select('id')\
            .eq('chalet_id', chalet_id)\
            .eq('status', 'confirmed')\
            .execute()
        
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        booking_dates = []
        if booking_ids:
            dates = supabase.table('booked_dates')\
                .select('date')\
                .eq('chalet_id', chalet_id)\
                .in_('booking_id', booking_ids)\
                .execute()
            booking_dates = [d['date'] for d in dates.data] if dates.data else []
        
        # التواريخ من المالك
        owner_dates = supabase.table('owner_booked_dates')\
            .select('date')\
            .eq('chalet_id', chalet_id)\
            .execute()
        owner_dates_list = [d['date'] for d in owner_dates.data] if owner_dates.data else []
        
        all_dates = booking_dates + owner_dates_list
        return all_dates
    except Exception as e:
        print(f"خطأ في get_all_booked_dates: {e}")
        return []

def check_availability_with_owner_dates(chalet_id, start_date, end_date):
    """التحقق من التوفر مع تواريخ المالك"""
    try:
        # التحقق من تواريخ المالك
        owner_dates = supabase.table('owner_booked_dates')\
            .select('date')\
            .eq('chalet_id', chalet_id)\
            .gte('date', start_date)\
            .lte('date', end_date)\
            .execute()
        
        if owner_dates.data:
            return False
        
        # التحقق من الحجوزات المؤكدة
        confirmed_bookings = supabase.table('bookings')\
            .select('id')\
            .eq('chalet_id', chalet_id)\
            .eq('status', 'confirmed')\
            .execute()
        
        booking_ids = [b['id'] for b in confirmed_bookings.data] if confirmed_bookings.data else []
        
        if booking_ids:
            booked_dates = supabase.table('booked_dates')\
                .select('date')\
                .eq('chalet_id', chalet_id)\
                .gte('date', start_date)\
                .lte('date', end_date)\
                .in_('booking_id', booking_ids)\
                .execute()
            
            if booked_dates.data:
                return False
        
        return True
    except Exception as e:
        print(f"خطأ في check_availability_with_owner_dates: {e}")
        return False

def get_bookings():
    """الحصول على جميع الحجوزات"""
    try:
        bookings = supabase.table('bookings')\
            .select('*, chalets(name_ar as chalet_name_ar, name_en as chalet_name_en), users!bookings_customer_id_fkey(name as customer_name, phone as customer_phone, national_id as customer_national_id), users!bookings_chalet_owner_id_fkey(name as owner_name, phone as owner_phone)')\
            .order('created_at', desc=True)\
            .execute()
        return bookings.data if bookings.data else []
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
        
        bookings = supabase.table('bookings')\
            .select('*, chalets(name_ar as chalet_name_ar, name_en as chalet_name_en), users!bookings_customer_id_fkey(name as customer_name, phone as customer_phone, national_id as customer_national_id)')\
            .in_('chalet_id', chalet_ids)\
            .order('created_at', desc=True)\
            .execute()
        return bookings.data if bookings.data else []
    except Exception as e:
        print(f"خطأ في get_bookings_by_owner: {e}")
        return []

def get_bookings_by_customer(customer_id):
    """الحصول على حجوزات العميل"""
    try:
        bookings = supabase.table('bookings')\
            .select('*, chalets(name_ar as chalet_name_ar, name_en as chalet_name_en, image as chalet_image), users!bookings_chalet_owner_id_fkey(name as owner_name, phone as owner_phone)')\
            .eq('customer_id', customer_id)\
            .order('created_at', desc=True)\
            .execute()
        return bookings.data if bookings.data else []
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
        booking = supabase.table('bookings')\
            .select('*, chalets(*), users!bookings_customer_id_fkey(*), users!bookings_chalet_owner_id_fkey(*)')\
            .eq('id', booking_id)\
            .execute()
        return booking.data[0] if booking.data else None
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
        
        bookings = supabase.table('bookings')\
            .select('*, chalets(name_ar as chalet_name_ar, name_en as chalet_name_en), users!bookings_customer_id_fkey(name as customer_name, phone as customer_phone, national_id as customer_national_id)')\
            .in_('chalet_id', chalet_ids)\
            .eq('status', 'pending')\
            .order('created_at', desc=True)\
            .execute()
        return bookings.data if bookings.data else []
    except Exception as e:
        print(f"خطأ في get_pending_bookings_by_owner: {e}")
        return []

def get_bookings_by_owner_all(owner_id):
    """الحصول على جميع حجوزات شاليهات المالك"""
    try:
        chalets = supabase.table('chalets').select('id').eq('owner_id', owner_id).execute()
        chalet_ids = [c['id'] for c in chalets.data] if chalets.data else []
        
        if not chalet_ids:
            return []
        
        bookings = supabase.table('bookings')\
            .select('*, chalets(name_ar as chalet_name_ar, name_en as chalet_name_en), users!bookings_customer_id_fkey(name as customer_name, phone as customer_phone, national_id as customer_national_id)')\
            .in_('chalet_id', chalet_ids)\
            .order('created_at', desc=True)\
            .execute()
        return bookings.data if bookings.data else []
    except Exception as e:
        print(f"خطأ في get_bookings_by_owner_all: {e}")
        return []

def update_booking_status_by_owner(booking_id, status, owner_id):
    """تحديث حالة الحجز من قبل المالك مع التحقق من الملكية"""
    try:
        # التحقق من أن الحجز يخص المالك
        booking = supabase.table('bookings')\
            .select('*, chalets(owner_id)')\
            .eq('id', booking_id)\
            .execute()
        
        if not booking.data or booking.data[0]['chalets']['owner_id'] != owner_id:
            return False
        
        # إذا كان الحجز مؤكداً وتم إلغاؤه، حذف التواريخ المحجوزة
        if booking.data[0]['status'] == 'confirmed' and status == 'cancelled':
            supabase.table('booked_dates').delete().eq('booking_id', booking_id).execute()
        
        supabase.table('bookings').update({'status': status}).eq('id', booking_id).execute()
        return True
    except Exception as e:
        print(f"خطأ في update_booking_status_by_owner: {e}")
        return False

# --- دوال الإحصائيات ---

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
