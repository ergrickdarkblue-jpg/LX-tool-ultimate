"""
Main Application Module - LX Tool Ultimate

Ứng dụng Flask chính cho Phone Farm Management.

Tính năng:
- WebSocket real-time communication
- REST API endpoints
- Static files serving
- Device management
- Task management
- Screenshot management
"""

import os
import sys
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, jsonify, request, send_file, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.exceptions import HTTPException

# Import config và logger trước tiên
import config
import logger as logger_module


# ====================================================================
# INITIALIZE LOGGING
# ====================================================================

log = logger_module.initialize_logging()


# ====================================================================
# INITIALIZE FLASK APP
# ====================================================================

def create_app():
    """
    Factory function để tạo Flask app.
    
    Returns:
        Flask: App instance
    """
    
    app = Flask(
        __name__,
        static_folder=str(config.STATIC_DIR),
        template_folder=str(config.TEMPLATE_DIR),
        static_url_path="/static"
    )
    
    # Configuration
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_UPLOAD_SIZE
    app.config['JSON_SORT_KEYS'] = False
    
    return app


# Tạo app instance
app = create_app()

# ====================================================================
# INITIALIZE SOCKETIO
# ====================================================================

socketio = SocketIO(
    app,
    cors_allowed_origins=config.WEBSOCKET_CORS_ALLOWED_ORIGINS,
    ping_timeout=config.WEBSOCKET_HEARTBEAT,
    ping_interval=config.WEBSOCKET_HEARTBEAT,
    async_mode='threading'
)

# Dictionary để lưu connected clients
connected_clients = {}


# ====================================================================
# ERROR HANDLERS
# ====================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    log = logger_module.get_logger(__name__)
    log.warning(f"404 Not Found: {request.path}")
    return jsonify({
        "success": False,
        "error": "Not Found",
        "message": f"Endpoint {request.path} not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    log = logger_module.get_logger(__name__)
    log.error(f"500 Internal Server Error: {error}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all uncaught exceptions."""
    log = logger_module.get_logger(__name__)
    
    if isinstance(e, HTTPException):
        return jsonify({
            "success": False,
            "error": e.name,
            "message": e.description
        }), e.code
    
    log.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": str(e)
    }), 500


# ====================================================================
# BEFORE/AFTER REQUEST HANDLERS
# ====================================================================

@app.before_request
def before_request():
    """Chạy trước mỗi request."""
    request.start_time = datetime.now()


@app.after_request
def after_request(response):
    """Chạy sau mỗi request."""
    try:
        duration = (datetime.now() - request.start_time).total_seconds() * 1000
        log = logger_module.get_logger(__name__)
        log.debug(f"{request.method} {request.path} - {response.status_code} - {duration:.2f}ms")
    except:
        pass
    
    return response


# ====================================================================
# HEALTH CHECK ENDPOINT
# ====================================================================

@app.route("/", methods=["GET"])
def index():
    """Trang chủ - redirect đến dashboard."""
    return jsonify({
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200


# ====================================================================
# API ENDPOINTS - INFO
# ====================================================================

@app.route(f"{config.API_BASE_URL}/info", methods=["GET"])
def api_info():
    """Lấy thông tin ứng dụng."""
    log = logger_module.get_logger(__name__)
    log.info("API: GET /info")
    
    return jsonify({
        "success": True,
        "data": {
            "name": config.APP_NAME,
            "version": config.APP_VERSION,
            "description": config.APP_DESCRIPTION,
            "api_version": config.API_VERSION,
            "contact": config.CONTACT_EMAIL,
            "timestamp": datetime.now().isoformat()
        }
    }), 200


@app.route(f"{config.API_BASE_URL}/status", methods=["GET"])
def api_status():
    """Lấy trạng thái hệ thống."""
    log = logger_module.get_logger(__name__)
    log.info("API: GET /status")
    
    # Kiểm tra executables
    executables = config.validate_executables()
    
    return jsonify({
        "success": True,
        "data": {
            "status": "running",
            "executables": {
                "adb": executables["adb"][0],
                "scrcpy": executables["scrcpy"][0]
            },
            "connected_clients": len(connected_clients),
            "timestamp": datetime.now().isoformat()
        }
    }), 200


# ====================================================================
# STATIC FILES
# ====================================================================

@app.route("/static/<path:filename>", methods=["GET"])
def serve_static(filename):
    """Serve static files."""
    return send_from_directory(config.STATIC_DIR, filename)


@app.route("/screenshots/<path:filename>", methods=["GET"])
def serve_screenshot(filename):
    """Serve screenshot files."""
    return send_from_directory(config.SCREENSHOT_DIR, filename)


# ====================================================================
# WEBSOCKET EVENTS
# ====================================================================

@socketio.on('connect')
def on_connect():
    """Client kết nối."""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now().isoformat(),
        'ip': request.remote_addr
    }
    
    log = logger_module.get_logger(__name__)
    logger_module.log_websocket_connection(client_id, __name__)
    
    emit('connection_response', {
        'status': 'connected',
        'client_id': client_id,
        'server_time': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def on_disconnect():
    """Client ngắt kết nối."""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    
    log = logger_module.get_logger(__name__)
    logger_module.log_websocket_disconnection(client_id, __name__)


@socketio.on('ping')
def on_ping(data):
    """Heartbeat/Ping từ client."""
    client_id = request.sid
    emit('pong', {
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('message')
def on_message(data):
    """Nhận message từ client."""
    client_id = request.sid
    message_type = data.get('type', 'unknown')
    
    log = logger_module.get_logger(__name__)
    logger_module.log_websocket_message(client_id, message_type, __name__)
    
    # Broadcast message
    emit('message', {
        'client_id': client_id,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


# ====================================================================
# CLI COMMANDS
# ====================================================================

@app.cli.command()
def init_db():
    """Khởi tạo database."""
    print("Initializing database...")
    # TODO: Import database module khi có
    print("Database initialized!")


@app.cli.command()
def cleanup_logs():
    """Cleanup old log files."""
    print("Cleaning up old log files...")
    logger_module.cleanup_old_logs(days=30)
    print("Cleanup completed!")


# ====================================================================
# APPLICATION STARTUP
# ====================================================================

def startup():
    """Khởi tạo ứng dụng."""
    
    log.info("="*70)
    log.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    log.info("="*70)
    
    # Khởi tạo thư mục
    try:
        config.initialize_directories()
        log.info("✓ Directories initialized")
    except Exception as e:
        log.error(f"✗ Failed to initialize directories: {e}")
        return False
    
    # Kiểm tra executables
    try:
        executables = config.validate_executables()
        adb_ok, adb_path = executables["adb"]
        scrcpy_ok, scrcpy_path = executables["scrcpy"]
        
        if adb_ok:
            log.info(f"✓ ADB found: {adb_path}")
        else:
            log.warning("✗ ADB not found")
        
        if scrcpy_ok:
            log.info(f"✓ scrcpy found: {scrcpy_path}")
        else:
            log.warning("✗ scrcpy not found (optional)")
            
    except Exception as e:
        log.error(f"✗ Error checking executables: {e}")
    
    # Log thông tin cấu hình
    log.info(f"Flask Host: {config.FLASK_HOST}:{config.FLASK_PORT}")
    log.info(f"Debug Mode: {config.FLASK_DEBUG}")
    log.info(f"API Base: {config.API_BASE_URL}")
    
    log.info("="*70)
    log.info(f"Ready to accept connections!")
    log.info("="*70)
    
    return True


# ====================================================================
# MAIN
# ====================================================================

if __name__ == "__main__":
    
    # Khởi tạo
    if not startup():
        sys.exit(1)
    
    # Chạy ứng dụng
    try:
        socketio.run(
            app,
            host=config.FLASK_HOST,
            port=config.FLASK_PORT,
            debug=config.FLASK_DEBUG,
            use_reloader=False
        )
    except KeyboardInterrupt:
        log.info("\nShutting down...")
    except Exception as e:
        log.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
