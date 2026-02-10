from flask import Flask, request
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import psycopg2
import os
from datetime import timedelta
import hashlib

#----------------------------#
# INTEGRITY CONTROL
#----------------------------#
def verify_integrity():
    """
    Verify integrity of Flask application files.
    If baseline doesn't exist or is empty, generate it.
    """
    # Use absolute paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    baseline_file = os.path.join(BASE_DIR, 'integrity', 'files.sha256')
    
    # Files to track (using absolute paths)
    files_to_check = [
        os.path.join(BASE_DIR, '__init__.py'),
        os.path.join(BASE_DIR, 'routes.py'),
        os.path.join(BASE_DIR, 'wsgi_mtls.py')
    ]
    
    # Check if baseline exists and is not empty
    if not os.path.exists(baseline_file) or os.path.getsize(baseline_file) == 0:
        print("⚠️  No baseline found or baseline is empty. Generating new baseline...")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(baseline_file), exist_ok=True)
        
        # Generate hashes
        with open(baseline_file, 'w') as f:
            for filepath in files_to_check:
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as file:
                        file_hash = hashlib.sha256(file.read()).hexdigest()
                        # Store relative path for portability
                        rel_path = os.path.relpath(filepath, BASE_DIR)
                        f.write(f"{file_hash}  {rel_path}\n")
                        print(f"  ✓ Hashed: {rel_path}")
        
        print(f"✅ Baseline created: {baseline_file}")
        print("⚠️  IMPORTANT: Review and secure this baseline file!")
        return  # Skip verification on first run
    
    # Verify existing baseline
    print("==> Verifying Flask application integrity...")
    
    with open(baseline_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
                
            expected_hash, rel_filepath = parts
            filepath = os.path.join(BASE_DIR, rel_filepath)
            
            if not os.path.exists(filepath):
                raise RuntimeError(f"❌ File missing: {filepath}")
            
            with open(filepath, 'rb') as file:
                actual_hash = hashlib.sha256(file.read()).hexdigest()
                
            if actual_hash != expected_hash:
                raise RuntimeError(f"❌ File integrity check failed for: {filepath}")
    
    print("✅ Flask application integrity verified")

#----------------------------#
# CSRF ATTACK PROTECTION
#----------------------------#
csrf = CSRFProtect()

from flask_limiter.util import get_remote_address

#----------------------------#
# RATE-LIMITING
#----------------------------#
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"],
    storage_uri="memory://"
)

#----------------------------#
# DATABASE CONNECTION
#----------------------------#
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),        
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=5432,
        sslmode='require',
        sslrootcert='/shared/certs/root.crt'
    )


#----------------------------#
# APP FACTORY
#----------------------------#
def create_app():
    verify_integrity()
    app = Flask(__name__)

    #----------------------------#
    # COOKIES
    #----------------------------#
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", os.urandom(32))
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)

    
    #----------------------------#
    # HEADERS SECURITY
    #----------------------------#
    Talisman(
        app,
        content_security_policy={
            "default-src": "'self'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data:"
        },
        force_https=False,
        strict_transport_security=False
    )

    csrf.init_app(app)
    limiter.init_app(app)

    from app.routes import bp
    app.register_blueprint(bp)

    return app


app = create_app()
