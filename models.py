# models.py
import enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo

def jakarta_now():
    return datetime.now(ZoneInfo("Asia/Jakarta"))

# Enum untuk tipe peran pengguna
class UserRole(enum.Enum):
    SUPERADMIN = 'SUPERADMIN'
    ADMIN = 'ADMIN'
    TEACHER = 'TEACHER'
    STUDENT = 'STUDENT'

# Enum untuk status kehadiran
class AttendanceStatus(enum.Enum):
    HADIR = 'hadir'
    IZIN = 'izin'
    SAKIT = 'sakit'
    ALPHA = 'alpha'

# Enum untuk tipe event
class EventType(enum.Enum):
    ACARA = 'ACARA'
    LIBUR = 'LIBUR'
    UJIAN = 'UJIAN'

# Model dasar untuk semua model yang membutuhkan multi-tenant
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=jakarta_now)
    updated_at = db.Column(db.DateTime, default=jakarta_now, onupdate=jakarta_now)

# Model untuk sekolah/tenant
class School(BaseModel):
    __tablename__ = 'schools'
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True) # <-- Index ditambahkan
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True) # <-- Index ditambahkan
    
    # Pengaturan branding sekolah
    brand_name = db.Column(db.String(100))
    primary_color = db.Column(db.String(7), default='#0d6efd')
    secondary_color = db.Column(db.String(7), default='#6c757d')
    logo_url = db.Column(db.String(200))
    
    # Relationship
    users = db.relationship('User', backref='school', lazy=True)
    classrooms = db.relationship('Classroom', backref='school', lazy=True)
    events = db.relationship('SchoolEvent', backref='school', lazy=True)

# Model untuk pengguna
class User(BaseModel, UserMixin):
    __tablename__ = 'users'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True, index=True) # <-- Index ditambahkan
    username = db.Column(db.String(80), unique=True, nullable=False, index=True) # <-- Index ditambahkan
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) # <-- Index ditambahkan
    password_hash = db.Column(db.Text)
    role = db.Column(db.Enum(UserRole), nullable=False, index=True) # <-- Index ditambahkan
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Relationship
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Model untuk guru/staff
class Teacher(BaseModel):
    __tablename__ = 'teachers'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) # <-- Index ditambahkan
    nip = db.Column(db.String(20), index=True) # <-- Index ditambahkan
    full_name = db.Column(db.String(100), nullable=False)
    is_homeroom = db.Column(db.Boolean, default=False)
    
    # Relationship
    homeroom_class = db.relationship('Classroom', backref='homeroom_teacher', uselist=False)
    recorded_attendances = db.relationship('Attendance', backref='teacher', lazy=True, cascade="all, delete-orphan")

# Model untuk siswa
class Student(BaseModel):
    __tablename__ = 'students'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True) # <-- Index ditambahkan
    nis = db.Column(db.String(20), nullable=False, index=True) # <-- Index ditambahkan
    nisn = db.Column(db.String(20), index=True) # <-- Index ditambahkan
    full_name = db.Column(db.String(100), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), index=True) # <-- Index ditambahkan
    qr_code = db.Column(db.String(100), unique=True)
    
    # Relationship
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade="all, delete-orphan")

# Model untuk kelas
class Classroom(BaseModel):
    __tablename__ = 'classrooms'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    name = db.Column(db.String(50), nullable=False)
    grade_level = db.Column(db.String(20))
    homeroom_teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), index=True) # <-- Index ditambahkan
    
    # Relationship
    students = db.relationship('Student', backref='classroom', lazy=True)
    attendance_records = db.relationship('Attendance', backref='classroom', lazy=True)

# Model untuk absensi
class Attendance(BaseModel):
    __tablename__ = 'attendances'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True) # <-- Index ditambahkan
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False, index=True) # <-- Index ditambahkan
    date = db.Column(db.Date, nullable=False, index=True) # <-- Index ditambahkan
    status = db.Column(db.Enum(AttendanceStatus), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    notes = db.Column(db.Text)

# Model untuk event sekolah
class SchoolEvent(BaseModel):
    __tablename__ = 'school_events'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False, index=True) # <-- Index ditambahkan
    end_date = db.Column(db.DateTime, nullable=False, index=True) # <-- Index ditambahkan
    event_type = db.Column(db.Enum(EventType), nullable=False)
    is_holiday = db.Column(db.Boolean, default=False)

# Model untuk QR code sekolah (untuk absensi guru)
class SchoolQRCode(BaseModel):
    __tablename__ = 'school_qr_codes'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, unique=True)
    qr_code = db.Column(db.String(100), unique=True)
    is_active = db.Column(db.Boolean, default=True)

# Model untuk absensi guru
class TeacherAttendance(BaseModel):
    __tablename__ = 'teacher_attendances'
    
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, index=True) # <-- Index ditambahkan
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False, index=True) # <-- Index ditambahkan
    date = db.Column(db.Date, nullable=False, index=True) # <-- Index ditambahkan
    time_in = db.Column(db.DateTime)
    time_out = db.Column(db.DateTime)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.HADIR)
    
    # Relationship
    teacher = db.relationship('Teacher', backref='attendance_records', lazy=True)

class SubscriptionPlan(enum.Enum):
    BASIC = 'basic'
    STANDARD = 'standard'
    PREMIUM = 'premium'

class SchoolSubscription(db.Model):
    __tablename__ = 'school_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False, unique=True)
    plan = db.Column(db.Enum(SubscriptionPlan), nullable=False, default=SubscriptionPlan.BASIC)
    is_active = db.Column(db.Boolean, default=True, index=True) # <-- Index ditambahkan
    start_date = db.Column(db.Date, nullable=False, index=True) # <-- Index ditambahkan
    end_date = db.Column(db.Date, nullable=False, index=True) # <-- Index ditambahkan
    max_teachers = db.Column(db.Integer, default=5)
    max_students = db.Column(db.Integer, default=100)
    features = db.Column(db.JSON, default=dict)
    
    # Relationship
    school = db.relationship('School', backref=db.backref('subscription', uselist=False))
    
    def is_valid(self):
        return self.is_active and jakarta_now().date() <= self.end_date
    
    def days_remaining(self):
        if not self.is_valid():
            return 0
        return (self.end_date - jakarta_now().date()).days