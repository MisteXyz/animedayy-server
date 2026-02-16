from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os
import sys
import secrets
import string

app = Flask(__name__)

# ✅ RAILWAY: Get port from environment variable
PORT = int(os.environ.get('PORT', 5000))

# ✅ RAILWAY: Determine file paths based on environment
def get_data_file_path():
    """Determine the correct path based on environment"""
    
    # Check if running on Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        # Railway: use volume mount if available, otherwise current directory
        volume_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_path:
            return os.path.join(volume_path, 'update_info.json')
        return '/app/update_info.json'
    
    # Check if running on PythonAnywhere
    if 'PYTHONANYWHERE_DOMAIN' in os.environ:
        return 'update_info.json'
    
    # Check if /tmp exists (Vercel, other platforms)
    if os.path.exists('/tmp'):
        return '/tmp/update_info.json'
    
    # Default: current directory (local development)
    return 'update_info.json'

def get_license_file_path():
    """Get path for license data file"""
    base_path = get_data_file_path()
    return base_path.replace('update_info.json', 'licenses.json')

UPDATE_DATA_FILE = get_data_file_path()
LICENSE_DATA_FILE = get_license_file_path()

def get_default_data():
    """Get default update data"""
    return {
        'version_code': 1,
        'version_name': '1.0.0',
        'update_required': False,
        'update_title': '',
        'update_message': '',
        'download_url': '',
        'whats_new': [],
        'maintenance_mode': False,
        'maintenance_title': 'Aplikasi Sedang Maintenance',
        'maintenance_message': 'Mohon maaf, aplikasi sedang dalam perbaikan. Silakan coba beberapa saat lagi.',
        'maintenance_estimated_end': '',
        'last_updated': datetime.now().isoformat()
    }

def get_default_license_data():
    """Get default license data structure"""
    return {
        'licenses': [],
        'last_updated': datetime.now().isoformat()
    }

# Initialize data files
def init_update_file():
    """Initialize update file with default data"""
    try:
        # Create directory if doesn't exist (for Railway volume)
        os.makedirs(os.path.dirname(UPDATE_DATA_FILE), exist_ok=True)
    except:
        pass
        
    if not os.path.exists(UPDATE_DATA_FILE):
        with open(UPDATE_DATA_FILE, 'w') as f:
            json.dump(get_default_data(), f, indent=2)
    else:
        try:
            with open(UPDATE_DATA_FILE, 'r') as f:
                content = f.read().strip()
                if not content:
                    raise ValueError("Empty file")
                data = json.loads(content)
                
                # Add maintenance fields if they don't exist
                updated = False
                if 'maintenance_mode' not in data:
                    data['maintenance_mode'] = False
                    updated = True
                if 'maintenance_title' not in data:
                    data['maintenance_title'] = 'Aplikasi Sedang Maintenance'
                    updated = True
                if 'maintenance_message' not in data:
                    data['maintenance_message'] = 'Mohon maaf, aplikasi sedang dalam perbaikan. Silakan coba beberapa saat lagi.'
                    updated = True
                if 'maintenance_estimated_end' not in data:
                    data['maintenance_estimated_end'] = ''
                    updated = True
                
                if updated:
                    with open(UPDATE_DATA_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
                        
        except (ValueError, json.JSONDecodeError):
            with open(UPDATE_DATA_FILE, 'w') as f:
                json.dump(get_default_data(), f, indent=2)

def init_license_file():
    """Initialize license file"""
    try:
        os.makedirs(os.path.dirname(LICENSE_DATA_FILE), exist_ok=True)
    except:
        pass
        
    if not os.path.exists(LICENSE_DATA_FILE):
        with open(LICENSE_DATA_FILE, 'w') as f:
            json.dump(get_default_license_data(), f, indent=2)

# Initialize files on startup
init_update_file()
init_license_file()

def load_update_info():
    """Load update info from JSON file"""
    try:
        with open(UPDATE_DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                default_data = get_default_data()
                save_update_info(default_data)
                return default_data
            data = json.loads(content)
            
            # Ensure maintenance fields exist
            if 'maintenance_mode' not in data:
                data['maintenance_mode'] = False
            if 'maintenance_title' not in data:
                data['maintenance_title'] = 'Aplikasi Sedang Maintenance'
            if 'maintenance_message' not in data:
                data['maintenance_message'] = 'Mohon maaf, aplikasi sedang dalam perbaikan. Silakan coba beberapa saat lagi.'
            if 'maintenance_estimated_end' not in data:
                data['maintenance_estimated_end'] = ''
                
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading update info: {e}")
        default_data = get_default_data()
        save_update_info(default_data)
        return default_data

def save_update_info(data):
    """Save update info to JSON file"""
    try:
        data['last_updated'] = datetime.now().isoformat()
        with open(UPDATE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving update info: {e}")
        return False

def load_licenses():
    """Load license data from JSON file"""
    try:
        with open(LICENSE_DATA_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                default_data = get_default_license_data()
                save_licenses(default_data)
                return default_data
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        default_data = get_default_license_data()
        save_licenses(default_data)
        return default_data

def save_licenses(data):
    """Save license data to JSON file"""
    try:
        data['last_updated'] = datetime.now().isoformat()
        with open(LICENSE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving licenses: {e}")
        return False

def generate_license_code(length=16):
    """Generate random license code"""
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    return '-'.join([code[i:i+4] for i in range(0, len(code), 4)])

# ===========================================
# HEALTH CHECK (untuk Railway)
# ===========================================
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'environment': os.environ.get('RAILWAY_ENVIRONMENT', 'local'),
        'timestamp': datetime.now().isoformat()
    })

# ===========================================
# API ENDPOINTS
# ===========================================

@app.route('/api/maintenance-status', methods=['GET'])
def maintenance_status():
    """Check if app is in maintenance mode"""
    update_info = load_update_info()
    return jsonify({
        'maintenance_mode': update_info.get('maintenance_mode', False),
        'maintenance_title': update_info.get('maintenance_title', ''),
        'maintenance_message': update_info.get('maintenance_message', ''),
        'maintenance_estimated_end': update_info.get('maintenance_estimated_end', '')
    })

@app.route('/api/check-update', methods=['GET'])
def check_update():
    """Check if there's an app update available"""
    try:
        current_version_code = int(request.args.get('current_version_code', 0))
        update_info = load_update_info()
        
        latest_version_code = update_info.get('version_code', 1)
        has_update = current_version_code < latest_version_code
        
        return jsonify({
            'has_update': has_update,
            'latest_version_code': latest_version_code,
            'latest_version_name': update_info.get('version_name', '1.0.0'),
            'update_required': update_info.get('update_required', False),
            'update_title': update_info.get('update_title', ''),
            'update_message': update_info.get('update_message', ''),
            'download_url': update_info.get('download_url', ''),
            'whats_new': update_info.get('whats_new', [])
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/validate-license', methods=['POST'])
def validate_license():
    """Validate and activate license with device"""
    try:
        data = request.get_json()
        license_code = data.get('license_code', '').strip().upper()
        device_id = data.get('device_id', '').strip()
        device_name = data.get('device_name', 'Unknown Device')
        
        if not license_code or not device_id:
            return jsonify({
                'success': False,
                'message': 'Kode lisensi dan Device ID harus diisi'
            }), 400
        
        license_data = load_licenses()
        
        # Cari lisensi
        license_obj = None
        for lic in license_data['licenses']:
            if lic['code'] == license_code:
                license_obj = lic
                break
        
        if not license_obj:
            return jsonify({
                'success': False,
                'message': 'Kode lisensi tidak valid'
            })
        
        # Cek status lisensi
        if license_obj['status'] == 'revoked':
            return jsonify({
                'success': False,
                'message': 'Kode lisensi sudah dicabut oleh admin'
            })
        
        if license_obj['status'] == 'used':
            if license_obj['device_id'] == device_id:
                return jsonify({
                    'success': True,
                    'message': 'Lisensi valid untuk perangkat ini',
                    'license_info': {
                        'code': license_obj['code'],
                        'activated_at': license_obj['activated_at'],
                        'device_name': license_obj['device_name']
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Kode lisensi sudah digunakan di perangkat lain ({license_obj["device_name"]})'
                })
        
        # Aktivasi lisensi
        if license_obj['status'] == 'active':
            license_obj['status'] = 'used'
            license_obj['device_id'] = device_id
            license_obj['device_name'] = device_name
            license_obj['activated_at'] = datetime.now().isoformat()
            
            save_licenses(license_data)
            
            return jsonify({
                'success': True,
                'message': 'Lisensi berhasil diaktifkan untuk perangkat ini',
                'license_info': {
                    'code': license_obj['code'],
                    'activated_at': license_obj['activated_at'],
                    'device_name': license_obj['device_name']
                }
            })
        
        return jsonify({
            'success': False,
            'message': 'Status lisensi tidak valid'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/check-license', methods=['POST'])
def check_license():
    """Check if device license is still valid"""
    try:
        data = request.get_json()
        device_id = data.get('device_id', '').strip()
        
        if not device_id:
            return jsonify({
                'valid': False,
                'message': 'Device ID tidak valid'
            })
        
        license_data = load_licenses()
        
        for license_obj in license_data['licenses']:
            if license_obj['device_id'] == device_id and license_obj['status'] == 'used':
                return jsonify({
                    'valid': True,
                    'message': 'Lisensi aktif',
                    'license_info': {
                        'code': license_obj['code'],
                        'activated_at': license_obj['activated_at'],
                        'device_name': license_obj['device_name']
                    }
                })
        
        return jsonify({
            'valid': False,
            'message': 'Lisensi tidak ditemukan atau sudah dicabut'
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'message': f'Error: {str(e)}'
        }), 500

# ===========================================
# ADMIN PANEL
# ===========================================
@app.route('/')
def admin_panel():
    """Admin panel"""
    update_info = load_update_info()
    license_data = load_licenses()
    
    total_licenses = len(license_data['licenses'])
    active_licenses = len([l for l in license_data['licenses'] if l['status'] == 'active'])
    used_licenses = len([l for l in license_data['licenses'] if l['status'] == 'used'])
    
    stats = {
        'total': total_licenses,
        'active': active_licenses,
        'used': used_licenses
    }
    
    return render_template('admin.html', 
                         update_info=update_info, 
                         licenses=license_data['licenses'],
                         stats=stats)

# ... (rest of your admin routes: /admin/update, /admin/license/add, etc.)
# Copy dari app.py original Anda

if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f"📱 AnimeDayy Update & License Manager")
    print(f"{'='*60}")
    print(f"📁 Update Data: {UPDATE_DATA_FILE}")
    print(f"🔑 License Data: {LICENSE_DATA_FILE}")
    print(f"🌐 Server: http://0.0.0.0:{PORT}")
    print(f"🚂 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    print(f"💾 Volume Mount: {os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', 'Not configured')}")
    print(f"{'='*60}\n")
    
    # ✅ Production mode for Railway
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(host='0.0.0.0', port=PORT, debug=debug_mode)
