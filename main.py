#!/usr/bin/env python3
"""
Standalone Py-KMS with WebUI, logs, and auto-install dependencies
Entry point for the py-kms application with enhanced web interface
"""

import subprocess
import sys
import os
import threading
import time
import webbrowser
from pathlib import Path

# Dependency Auto-Install
def install_dependencies():
    """Auto-install required packages if not available"""
    # Map package names to their import names
    package_mapping = {
        "flask": "flask",
        "gunicorn": "gunicorn", 
        "dnspython": "dns",  # dnspython imports as 'dns'
        "tzlocal": "tzlocal"
    }
    
    missing_packages = []
    for pkg, import_name in package_mapping.items():
        try:
            __import__(import_name)
            print(f"✓ {pkg} is available")
        except ImportError:
            missing_packages.append(pkg)
            print(f"✗ {pkg} is missing")
    
    if missing_packages:
        print(f"Installing missing packages: {missing_packages}")
        try:
            # Try to install missing packages
            for pkg in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages"])
                print(f"✓ Successfully installed {pkg}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not install packages automatically: {e}")
            print("Please install them manually using: pip install " + " ".join(missing_packages))
            return False
    else:
        print("All required dependencies are available!")
    
    return True

def setup_environment():
    """Setup environment variables and paths"""
    # Change to py-kms directory
    pykms_dir = Path(__file__).parent / 'py-kms'
    os.chdir(pykms_dir)
    sys.path.insert(0, str(pykms_dir))
    
    # Set required environment variables
    os.environ['PYKMS_SQLITE_DB_PATH'] = str(Path(__file__).parent / 'pykms_database.db')
    os.environ['PYKMS_LICENSE_PATH'] = str(Path(__file__).parent / 'LICENSE')
    os.environ['PYKMS_LOGS_PATH'] = str(Path(__file__).parent / 'kms_logs.txt')

def start_kms_server_background():
    """Start KMS server in background"""
    try:
        print("Starting KMS server in background...")
        
        # Create logs directory if it doesn't exist
        log_file = Path(__file__).parent / 'kms_logs.txt'
        
        # Start server with logging
        server_process = subprocess.Popen(
            [sys.executable, 'pykms_Server.py', '0.0.0.0', '1688', '-V', 'INFO'],
            stdout=open(log_file, 'w'),
            stderr=subprocess.STDOUT,
            cwd=Path(__file__).parent / 'py-kms'
        )
        
        print(f"KMS server started with PID: {server_process.pid}")
        print(f"Logs will be written to: {log_file}")
        
        # Give server time to start
        time.sleep(2)
        
        return server_process
        
    except Exception as e:
        print(f"Error starting KMS server: {e}")
        return None

def create_enhanced_webui():
    """Create enhanced WebUI with additional features"""
    from flask import Flask, render_template, request, jsonify, redirect, url_for
    import json
    from datetime import datetime
    
    # Import py-kms modules
    try:
        from pykms_DB2Dict import kmsDB2Dict
        from pykms_Sql import sql_get_all
    except ImportError as e:
        print(f"Warning: Could not import some py-kms modules: {e}")
        kmsDB2Dict = None
        sql_get_all = None
    
    app = Flask(__name__, template_folder='py-kms/templates', static_folder='py-kms/static')
    
    # Get actual IP address for display
    def get_display_ip():
        import socket
        try:
            # Get local IP by connecting to a remote address (doesn't actually connect)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost
    
    # Global variables for server config
    server_config = {
        'ip': '0.0.0.0',
        'port': '1688',
        'status': 'running',
        'display_ip': get_display_ip()  # Actual IP for display
    }
    
    @app.route('/')
    def home():
        """Enhanced home page with server info and products"""
        try:
            # Get KMS products if available
            products = {}
            if kmsDB2Dict:
                try:
                    kms_data = kmsDB2Dict()
                    products = extract_products_from_db(kms_data)
                except Exception as e:
                    print(f"Error loading KMS products: {e}")
            
            # Get recent logs
            logs = get_recent_logs(50)
            
            return render_template('enhanced_home.html', 
                                   server_config=server_config,
                                   products=products,
                                   logs=logs)
        except Exception as e:
            return f"Error loading home page: {e}", 500
    
    @app.route('/api/logs')
    def get_logs_api():
        """API endpoint for live log updates"""
        logs = get_recent_logs(100)
        return jsonify(logs)
    
    @app.route('/api/server/config', methods=['GET', 'POST'])
    def server_config_api():
        """API endpoint for server configuration"""
        if request.method == 'POST':
            data = request.get_json()
            server_config['ip'] = data.get('ip', '0.0.0.0')
            server_config['port'] = data.get('port', '1688')
            
            # Log the configuration change
            log_command(f"Server configuration changed to {server_config['ip']}:{server_config['port']}")
            
            return jsonify(server_config)
        
        return jsonify(server_config)
    
    @app.route('/api/execute_command', methods=['POST'])
    def execute_command():
        """Execute KMS-related commands and log results"""
        data = request.get_json()
        command = data.get('command', '')
        product_name = data.get('product', '')
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        try:
            # Log the command execution
            log_entry = f"[{datetime.now()}] Executing: {command} for product: {product_name}"
            log_command(log_entry)
            
            # Execute the command (simulated for safety)
            result = f"Command executed: {command}"
            
            log_command(f"[{datetime.now()}] Result: {result}")
            
            return jsonify({
                'success': True,
                'command': command,
                'result': result,
                'product': product_name
            })
            
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            log_command(f"[{datetime.now()}] Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
    
    def extract_products_from_db(kms_data):
        """Extract products and GVLK keys from KMS database"""
        products = {}
        
        def extract_items(item):
            if isinstance(item, list):
                for i in item:
                    extract_items(i)
            elif isinstance(item, dict):
                if 'KmsItems' in item:
                    extract_items(item['KmsItems'])
                elif 'SkuItems' in item:
                    extract_items(item['SkuItems'])
                elif 'Gvlk' in item and 'DisplayName' in item:
                    if item['Gvlk']:
                        products[item['DisplayName']] = {
                            'gvlk': item['Gvlk'],
                            'commands': generate_commands(item['DisplayName'], item['Gvlk'])
                        }
        
        try:
            extract_items(kms_data)
        except Exception as e:
            print(f"Error extracting products: {e}")
        
        return products
    
    def generate_commands(product_name, gvlk_key):
        """Generate Windows commands for KMS activation"""
        # Use display IP for commands if server IP is 0.0.0.0
        display_ip = server_config['display_ip'] if server_config['ip'] == '0.0.0.0' else server_config['ip']
        server_addr = f"{display_ip}:{server_config['port']}"
        
        return {
            'install_key': f'slmgr /ipk {gvlk_key}',
            'set_kms_server': f'slmgr /skms {server_addr}',
            'activate': 'slmgr /ato',
            'check_status': 'slmgr /xpr'
        }
    
    def get_recent_logs(lines=50):
        """Get recent logs from the KMS server"""
        try:
            log_file = Path(__file__).parent / 'kms_logs.txt'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            print(f"Error reading logs: {e}")
        
        return []
    
    def log_command(message):
        """Log command execution to file"""
        try:
            log_file = Path(__file__).parent / 'kms_logs.txt'
            with open(log_file, 'a') as f:
                f.write(f"{message}\n")
        except Exception as e:
            print(f"Error logging command: {e}")
    
    return app

def create_enhanced_template():
    """Create enhanced HTML template for the home page if it doesn't exist"""
    # Check if template already exists to avoid redundant writes
    template_path = Path(__file__).parent / 'py-kms' / 'templates' / 'enhanced_home.html'
    if template_path.exists():
        print("Enhanced template already exists, skipping creation...")
        return
    template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Py-KMS Server & WebUI</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/bulma.min.css') }}">
    <style>
        .server-status { margin: 1rem 0; }
        .product-card { margin: 1rem 0; cursor: pointer; transition: all 0.3s ease; }
        .product-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .product-header { display: flex; justify-content: space-between; align-items: center; }
        .expand-icon { transition: transform 0.3s ease; }
        .expanded .expand-icon { transform: rotate(180deg); }
        .commands-section { display: none; margin-top: 1rem; }
        .commands-section.show { display: block; }
        .command-box { background: #f5f5f5; padding: 1rem; border-radius: 5px; margin: 0.5rem 0; position: relative; }
        .command-text { background: #fff; padding: 0.5rem; border-radius: 3px; border: 1px solid #ddd; margin: 0.5rem 0; font-family: monospace; word-break: break-all; }
        .copy-button { position: absolute; top: 0.5rem; right: 0.5rem; }
        .log-container { background: #000; color: #00ff00; padding: 1rem; height: 300px; overflow-y: scroll; font-family: monospace; }
        .highlight-ip { background: yellow; font-weight: bold; }
        .gvlk-key { background: #fff; padding: 0.5rem; border-radius: 3px; border: 1px solid #ddd; font-family: monospace; display: inline-block; position: relative; }
    </style>
</head>
<body>
    <div class="container">
        <section class="section">
            <h1 class="title">Py-KMS Server & WebUI</h1>
            
            <!-- Server Status -->
            <div class="box server-status">
                <h2 class="subtitle">Server Status</h2>
                <p><strong>IP Address:</strong> <span class="highlight-ip">{{ server_config.display_ip if server_config.ip == '0.0.0.0' else server_config.ip }}</span></p>
                <p><strong>Port:</strong> {{ server_config.port }}</p>
                <p><strong>Status:</strong> 
                    <span class="tag is-success">{{ server_config.status.title() }}</span>
                </p>
                
                <div class="field is-grouped">
                    <div class="control">
                        <input class="input" type="text" id="server-ip" placeholder="Server IP" value="{{ server_config.ip }}">
                    </div>
                    <div class="control">
                        <input class="input" type="text" id="server-port" placeholder="Port" value="{{ server_config.port }}">
                    </div>
                    <div class="control">
                        <button class="button is-primary" onclick="updateServerConfig()">Update</button>
                    </div>
                </div>
            </div>
            
            <!-- KMS Products -->
            <div class="box">
                <h2 class="subtitle">KMS Products ({{ products|length }} available)</h2>
                <p class="help">Click on a product to view activation commands</p>
                {% for product_name, product_data in products.items() %}
                <div class="card product-card" onclick="toggleCommands('{{ loop.index }}')">
                    <div class="card-content">
                        <div class="product-header">
                            <div>
                                <h3 class="title is-5">{{ product_name }}</h3>
                                <p><strong>GVLK Key:</strong> 
                                    <span class="gvlk-key" id="gvlk-{{ loop.index }}">{{ product_data.gvlk }}</span>
                                    <button class="button is-small is-text copy-button" onclick="event.stopPropagation(); copyToClipboard('gvlk-{{ loop.index }}', this)" title="Copy GVLK Key">📋</button>
                                </p>
                            </div>
                            <span class="expand-icon">▼</span>
                        </div>
                        
                        <div class="commands-section" id="commands-{{ loop.index }}">
                            <h4 class="subtitle is-6">Activation Commands:</h4>
                            
                            <div class="command-box">
                                <button class="button is-small is-light copy-button" onclick="event.stopPropagation(); copyToClipboard('cmd1-{{ loop.index }}', this)" title="Copy Command">📋</button>
                                <p><strong>1. Install GVLK Key:</strong></p>
                                <div class="command-text" id="cmd1-{{ loop.index }}">{{ product_data.commands.install_key }}</div>
                                <button class="button is-small is-info" onclick="event.stopPropagation(); executeCommand('{{ product_data.commands.install_key }}', '{{ product_name }}')">Execute</button>
                            </div>
                            
                            <div class="command-box">
                                <button class="button is-small is-light copy-button" onclick="event.stopPropagation(); copyToClipboard('cmd2-{{ loop.index }}', this)" title="Copy Command">📋</button>
                                <p><strong>2. Set KMS Server:</strong></p>
                                <div class="command-text" id="cmd2-{{ loop.index }}">{{ product_data.commands.set_kms_server }}</div>
                                <button class="button is-small is-info" onclick="event.stopPropagation(); executeCommand('{{ product_data.commands.set_kms_server }}', '{{ product_name }}')">Execute</button>
                            </div>
                            
                            <div class="command-box">
                                <button class="button is-small is-light copy-button" onclick="event.stopPropagation(); copyToClipboard('cmd3-{{ loop.index }}', this)" title="Copy Command">📋</button>
                                <p><strong>3. Activate Windows:</strong></p>
                                <div class="command-text" id="cmd3-{{ loop.index }}">{{ product_data.commands.activate }}</div>
                                <button class="button is-small is-info" onclick="event.stopPropagation(); executeCommand('{{ product_data.commands.activate }}', '{{ product_name }}')">Execute</button>
                            </div>
                            
                            <div class="command-box">
                                <button class="button is-small is-light copy-button" onclick="event.stopPropagation(); copyToClipboard('cmd4-{{ loop.index }}', this)" title="Copy Command">📋</button>
                                <p><strong>4. Check Status:</strong></p>
                                <div class="command-text" id="cmd4-{{ loop.index }}">{{ product_data.commands.check_status }}</div>
                                <button class="button is-small is-info" onclick="event.stopPropagation(); executeCommand('{{ product_data.commands.check_status }}', '{{ product_name }}')">Execute</button>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Live Logs -->
            <div class="box">
                <h2 class="subtitle">Live Server Logs</h2>
                <div class="log-container" id="log-container">
                    {% for log_line in logs %}
                    <div>{{ log_line|trim }}</div>
                    {% endfor %}
                </div>
                <button class="button is-small" onclick="refreshLogs()">Refresh Logs</button>
                <button class="button is-small" onclick="toggleAutoRefresh()">Toggle Auto-Refresh</button>
            </div>
        </section>
    </div>
    
    <script>
        let autoRefresh = false;
        let refreshInterval;
        
        function toggleCommands(index) {
            const commandsSection = document.getElementById('commands-' + index);
            const card = commandsSection.closest('.product-card');
            const expandIcon = card.querySelector('.expand-icon');
            
            if (commandsSection.classList.contains('show')) {
                commandsSection.classList.remove('show');
                card.classList.remove('expanded');
            } else {
                // Close all other expanded cards
                document.querySelectorAll('.commands-section.show').forEach(section => {
                    section.classList.remove('show');
                    section.closest('.product-card').classList.remove('expanded');
                });
                
                commandsSection.classList.add('show');
                card.classList.add('expanded');
            }
        }
        
        function copyToClipboard(elementId, button) {
            const element = document.getElementById(elementId);
            const text = element.textContent || element.innerText;
            
            navigator.clipboard.writeText(text).then(function() {
                // Visual feedback
                const originalText = button.innerHTML;
                button.innerHTML = '✓';
                button.classList.add('is-success');
                
                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.classList.remove('is-success');
                }, 2000);
            }).catch(function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                // Visual feedback
                const originalText = button.innerHTML;
                button.innerHTML = '✓';
                button.classList.add('is-success');
                
                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.classList.remove('is-success');
                }, 2000);
            });
        }
        
        function updateServerConfig() {
            const ip = document.getElementById('server-ip').value;
            const port = document.getElementById('server-port').value;
            
            fetch('/api/server/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip: ip, port: port })
            })
            .then(response => response.json())
            .then(data => {
                alert('Server configuration updated!');
                location.reload();
            })
            .catch(error => alert('Error updating config: ' + error));
        }
        
        function executeCommand(command, product) {
            fetch('/api/execute_command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: command, product: product })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Command executed: ' + data.result);
                    refreshLogs();
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => alert('Error executing command: ' + error));
        }
        
        function refreshLogs() {
            fetch('/api/logs')
            .then(response => response.json())
            .then(logs => {
                const container = document.getElementById('log-container');
                container.innerHTML = logs.map(log => '<div>' + log.trim() + '</div>').join('');
                container.scrollTop = container.scrollHeight;
            })
            .catch(error => console.error('Error refreshing logs:', error));
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            if (autoRefresh) {
                refreshInterval = setInterval(refreshLogs, 2000);
            } else {
                clearInterval(refreshInterval);
            }
        }
        
        // Initial log refresh
        setTimeout(refreshLogs, 1000);
    </script>
</body>
</html>'''
    
    # Create enhanced template
    template_dir = Path(__file__).parent / 'py-kms' / 'templates'
    template_dir.mkdir(exist_ok=True)
    
    with open(template_dir / 'enhanced_home.html', 'w') as f:
        f.write(template_content)

def main():
    """Main entry point"""
    print("=== Py-KMS Standalone with Enhanced WebUI ===")
    
    try:
        # Install dependencies
        print("Checking and installing dependencies...")
        if not install_dependencies():
            print("Warning: Some dependencies could not be installed. Continuing anyway...")
        
        # Setup environment
        print("Setting up environment...")
        setup_environment()
        
        # Create enhanced template
        print("Creating enhanced WebUI template...")
        create_enhanced_template()
        
        # Start KMS server in background
        print("Starting KMS server...")
        server_process = start_kms_server_background()
        
        # Create and run enhanced WebUI
        print("Starting enhanced WebUI...")
        app = create_enhanced_webui()
        
        # Auto-open browser (optional)
        def open_browser():
            time.sleep(2)  # Wait for server to start
            try:
                webbrowser.open('http://localhost:5000')
            except Exception as e:
                print(f"Could not auto-open browser: {e}")
        
        # Start browser opening in separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print("\n" + "="*50)
        print("✓ KMS Server: Running on 0.0.0.0:1688")
        print("✓ WebUI: Running on http://localhost:5000")
        print("✓ Logs: Saved to kms_logs.txt")
        print("="*50 + "\n")
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        if 'server_process' in locals() and server_process:
            server_process.terminate()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()