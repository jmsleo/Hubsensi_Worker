# factory.py
import os
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for, send_from_directory, make_response, render_template_string
from flask_login import current_user, logout_user
from config import Config
from extensions import db, login_manager, migrate, csrf, cache
from models import User, UserRole, jakarta_now
from blueprints import init_app as init_blueprints
from celery_worker import celery

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inisialisasi semua ekstensi
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cache.init_app(app)

    # Perbarui konfigurasi Celery dari konfigurasi Flask
    celery.conf.update(app.config)

    # Buat ContextTask agar task Celery berjalan dalam konteks aplikasi
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # Inisialisasi semua blueprint
    init_blueprints(app)

    # User loader untuk Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Pengaturan Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'info'

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html', error=error if app.config['DEBUG'] else None), 500

    @app.errorhandler(503)
    def service_unavailable_error(error):
        return render_template('errors/503.html'), 503

    # Context Processor
    @app.context_processor
    def inject_school_data():
        school_data = {}
        if hasattr(request, 'school_id') and request.school_id:
            from models import School
            school = School.query.get(request.school_id)
            if school:
                school_data = {
                    'school': school,
                    'brand_name': school.brand_name or school.name,
                    'primary_color': school.primary_color or '#0d6efd',
                    'secondary_color': school.secondary_color or '#6c757d',
                    'logo_url': school.logo_url
                }
        return school_data
    
    @app.context_processor
    def inject_now():
        return {'now': jakarta_now()}

    # Middleware (Before Request)
    @app.before_request
    def check_subscription():
        if (current_user.is_anonymous or 
            current_user.role == UserRole.SUPERADMIN or
            request.endpoint in ['auth.logout', 'auth.login', 'static']):
            return
        
        if (current_user.school_id and 
            hasattr(current_user, 'school') and 
            current_user.school.subscription):
            
            subscription = current_user.school.subscription
            if not subscription.is_valid():
                flash('Langganan sekolah Anda telah kedaluwarsa. Silakan hubungi administrator.', 'warning')
                if request.endpoint not in ['auth.logout', 'auth.login']:
                    logout_user()
                    return redirect(url_for('auth.login'))

    @app.before_request
    def set_school_id():
        if current_user.is_authenticated and current_user.school_id:
            request.school_id = current_user.school_id
        else:
            request.school_id = None
    
    @app.before_request
    def check_registration_access():
        if request.endpoint == 'auth.register' and os.environ.get('ALLOW_PUBLIC_REGISTRATION', 'false').lower() != 'true':
            abort(404)

    # Route Utama
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.role == UserRole.SUPERADMIN:
                return redirect(url_for('superadmin.dashboard'))
            elif current_user.role == UserRole.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif current_user.role == UserRole.TEACHER:
                return redirect(url_for('teacher.dashboard'))
            elif current_user.role == UserRole.STUDENT:
                return redirect(url_for('student.dashboard'))
        return render_template('index.html')

    # Route untuk file statis di root
    @app.route('/robots.txt')
    def static_from_root():
        return send_from_directory(app.static_folder, request.path[1:])

    @app.route('/sitemap.xml')
    def sitemap():
        static_urls = [
            {'loc': url_for('index', _external=True)},
            {'loc': url_for('auth.login', _external=True)}
        ]
        xml_sitemap = render_template_string("""
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {% for url in urls %}
            <url>
                <loc>{{ url.loc }}</loc>
            </url>
        {% endfor %}
        </urlset>
        """, urls=static_urls)
        response = make_response(xml_sitemap)
        response.headers["Content-Type"] = "application/xml"
        return response

    # Health check untuk deployment
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200
    
    return app