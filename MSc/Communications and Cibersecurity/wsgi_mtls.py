import ssl
from werkzeug.serving import make_server
from app import app  

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

# Flask server certificate
context.load_cert_chain(
    certfile="/shared/certs/flask_server.crt", 
    keyfile="/private/flask_server.key"
)

# Trust Root CA for client certificates
context.load_verify_locations(cafile="/shared/certs/root.crt")

#----------------------------#
# mTLS - REQUIRE CLIENT CERT
#----------------------------#
context.verify_mode = ssl.CERT_REQUIRED
context.check_hostname = False 

# TLS 1.2 and 1.3
context.minimum_version = ssl.TLSVersion.TLSv1_2

if __name__ == "__main__":
    print("=" * 50)
    print("Flask with mTLS ENABLED")
    print("Client cert: REQUIRED")
    print("check_hostname: DISABLED")
    print("=" * 50)
    server = make_server("0.0.0.0", 8080, app, ssl_context=context)
    server.serve_forever()