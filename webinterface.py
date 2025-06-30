"""
Web Interface for WiFi to Ethernet Adapter
Optimized for Raspberry Pi Pico 2 W with MicroPython

This script creates a web server that displays:
1. Complete log of the Raspberry Pi
2. Status LEDs
3. IP addresses of all components

The UI is styled to look like Apple's "Liquid Glass" design.

PICO 2 W OPTIMIZATIONS:
- Reduced buffer sizes for better memory management
- Optimized socket configuration for MicroPython
- Improved garbage collection
- Reduced memory footprint
- Better error handling for limited resources

Template System:
---------------
The HTML template is stored in the file 'templates/template.html'.
This allows for easier editing and maintenance of the UI.
The template uses placeholders like {wifi_ip} that are replaced with actual values.

Development Tools:
----------------
The web interface includes development tools that make it easier to test changes:
1. API endpoint '/api/reload-template' to reload the template without restarting the server
2. A "Reload Template" button in the UI that calls this API endpoint

These development tools can be removed in production by:
1. Removing the development tools section from the template.html file
2. Removing the '/api/reload-template' API endpoint from the handle_request function
"""

import socket
import time
import json
from machine import Pin
import gc  # Garbage collection for Pico 2 W memory optimization

# Configuration optimized for Raspberry Pi Pico 2 W
WEB_SERVER_PORT = 80  # Standard HTTP port
MAX_LOG_ENTRIES = 50  # Reduced from 100 to 50 for better memory management on Pico 2 W
SOCKET_BUFFER_SIZE = 2048  # Reduced buffer size for Pico 2 W (was 8192)
REQUEST_TIMEOUT = 5  # Reduced timeout for better responsiveness
MAX_CONNECTIONS = 5  # Reduced from 20 to 5 for memory optimization

# Global variables
log_buffer = []
led_states = {
    "wifi": False,
    "ethernet": False,
    "data": False,
    "builtin": False
}
ip_addresses = {
    "wifi": "Unknown",
    "ethernet": "Unknown",
    "hue_bridge": "Unknown"
}
# Additional status information
ethernet_status = {
    "initialized": False,
    "link_status": False,
    "spi_config": "None",
    "error_message": "Not initialized"
}
# Template cache
template_cache = {
    "html": None,
    "loaded": False,
    "path": None
}

# Define the LEDs (same as in main.py and boot.py)
WIFI_LED_PIN = 28
ETH_LED_PIN = 27
DATA_LED_PIN = 26
BUILTIN_LED_PIN = 25  # Builtin LED on Raspberry Pi Pico

# Initialize the LEDs
led_wifi = Pin(WIFI_LED_PIN, Pin.OUT)
led_eth = Pin(ETH_LED_PIN, Pin.OUT)
led_data = Pin(DATA_LED_PIN, Pin.OUT)
led_builtin = Pin(BUILTIN_LED_PIN, Pin.OUT)

# Function to add a log entry
def add_log(message):
    global log_buffer
    timestamp = time.localtime()
    time_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        timestamp[0], timestamp[1], timestamp[2],
        timestamp[3], timestamp[4], timestamp[5]
    )
    log_entry = {"time": time_str, "message": message}
    log_buffer.append(log_entry)

    # Keep log buffer at maximum size
    if len(log_buffer) > MAX_LOG_ENTRIES:
        log_buffer.pop(0)

    # Don't print to console here as it causes duplication
    # The calling functions (log_message in main.py and boot_log in boot.py) already print to console

# Function to update LED states
def update_led_states():
    global led_states
    led_states["wifi"] = led_wifi.value()
    led_states["ethernet"] = led_eth.value()
    led_states["data"] = led_data.value()
    led_states["builtin"] = led_builtin.value()

# Function to update IP addresses
def update_ip_addresses(wifi_ip=None, ethernet_ip=None, hue_bridge_ip=None):
    global ip_addresses
    if wifi_ip:
        ip_addresses["wifi"] = wifi_ip
    if ethernet_ip:
        ip_addresses["ethernet"] = ethernet_ip
    if hue_bridge_ip:
        ip_addresses["hue_bridge"] = hue_bridge_ip

# Function to update Ethernet status
def update_ethernet_status(initialized=None, link_status=None, spi_config=None, error_message=None):
    global ethernet_status
    if initialized is not None:
        ethernet_status["initialized"] = initialized
    if link_status is not None:
        ethernet_status["link_status"] = link_status
    if spi_config is not None:
        ethernet_status["spi_config"] = spi_config
    if error_message is not None:
        ethernet_status["error_message"] = error_message

# Function to check if a file exists in MicroPython
def file_exists(filename):
    try:
        with open(filename, 'r') as f:
            return True
    except OSError:
        return False

# Function to reload the template (useful for development)
def reload_template():
    global template_cache
    add_log("Reloading template from file...")
    # Reset the cache
    template_cache["loaded"] = False
    template_cache["html"] = None
    template_cache["path"] = None
    # Read the template again
    return read_template()

# Function to read the HTML template from file
def read_template():
    global template_cache

    # If template is already loaded, return it from cache
    if template_cache["loaded"]:
        add_log(f"Using cached template from: {template_cache['path']}")
        return template_cache["html"]

    # Possible paths for the template file
    template_paths = [
        'templates/template.html',  # Relative path
        '/templates/template.html',  # Absolute path
        './templates/template.html',  # Explicit relative path
    ]

    # Check which path exists
    for path in template_paths:
        if file_exists(path):
            add_log(f"Template file found at: {path}")
            try:
                with open(path, 'r') as file:
                    template_html = file.read()
                    # Cache the template
                    template_cache["html"] = template_html
                    template_cache["loaded"] = True
                    template_cache["path"] = path
                    add_log(f"Template cached from: {path}")
                    return template_html
            except Exception as e:
                add_log(f"Error reading template file at {path}: {e}")
                # Continue to the next path
        else:
            add_log(f"Template file not found at: {path}")

    # If we get here, none of the paths worked
    add_log("All template paths failed, using fallback template")
    # Return a simple fallback template in case of error
    fallback_template = """<!DOCTYPE html>
<html>
<head><title>Raspberry Pi Adapter Status (Fallback)</title></head>
<body>
    <h1>Raspberry Pi Adapter Status</h1>
    <p>Error loading template. Please check the logs.</p>
</body>
</html>"""

    # Cache the fallback template
    template_cache["html"] = fallback_template
    template_cache["loaded"] = True
    template_cache["path"] = "fallback"

    return fallback_template

# HTML template with Apple's "Liquid Glass" style
def generate_html():
    update_led_states()

    # Read the HTML template from file
    add_log("Reading HTML template from file...")
    html = read_template()
    add_log(f"Template loaded successfully, size: {len(html)} bytes")

    # Set LED classes based on their states
    wifi_class = "on" if led_states["wifi"] else "off"
    ethernet_class = "on" if led_states["ethernet"] else "off"
    data_class = "on" if led_states["data"] else "off"
    builtin_class = "on" if led_states["builtin"] else "off"

    # Generate log entries HTML
    log_entries_html = ""
    for entry in reversed(log_buffer):
        log_entries_html += f'<div class="log-entry"><span class="log-time">{entry["time"]}</span>{entry["message"]}</div>\n'

    # Generate Ethernet status classes and messages
    eth_init_status = "Initialized" if ethernet_status["initialized"] else "Not Initialized"
    eth_init_class = "status-success" if ethernet_status["initialized"] else "status-error"

    eth_link_status = "Connected" if ethernet_status["link_status"] else "Disconnected"
    eth_link_class = "status-success" if ethernet_status["link_status"] else "status-warning"

    eth_spi_config = ethernet_status["spi_config"]

    eth_error_message = ethernet_status["error_message"]
    eth_error_class = "status-success" if eth_error_message == "None" else "status-error"

    # Replace placeholders in the template using string replacement instead of format
    replacements = {
        '{wifi_class}': wifi_class,
        '{ethernet_class}': ethernet_class,
        '{data_class}': data_class,
        '{builtin_class}': builtin_class,
        '{wifi_ip}': ip_addresses["wifi"],
        '{ethernet_ip}': ip_addresses["ethernet"],
        '{hue_bridge_ip}': ip_addresses["hue_bridge"],
        '{eth_init_status}': eth_init_status,
        '{eth_init_class}': eth_init_class,
        '{eth_link_status}': eth_link_status,
        '{eth_link_class}': eth_link_class,
        '{eth_spi_config}': eth_spi_config,
        '{eth_error_message}': eth_error_message,
        '{eth_error_class}': eth_error_class,
        '{log_entries}': log_entries_html
    }

    # Apply replacements
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return html

# Function to handle HTTP requests
def is_safari(request):
    """Check if the request is from Safari browser"""
    return "Safari" in request and "Chrome" not in request and "Edg" not in request

def handle_request(client_socket):
    try:
        # Set optimized timeout for receiving data on Pico 2 W
        client_socket.settimeout(REQUEST_TIMEOUT)  # Optimized timeout for better responsiveness

        try:
            # Try to receive and decode the request with optimized buffer for Pico 2 W
            request_data = client_socket.recv(SOCKET_BUFFER_SIZE)  # Optimized buffer size
            if not request_data:
                add_log("Empty request received")
                return

            # Try to decode as UTF-8, but handle decoding errors
            try:
                request = request_data.decode('utf-8')
            except UnicodeDecodeError:
                add_log("Warning: Could not decode request as UTF-8, using latin-1 instead")
                request = request_data.decode('latin-1')  # Fallback encoding

            # Parse the request to get the path
            request_lines = request.split('\r\n')
            if not request_lines:
                add_log("Malformed request: no request lines")
                return

            request_line = request_lines[0]
            parts = request_line.split(' ')
            if len(parts) < 3:
                add_log(f"Malformed request line: {request_line}")
                return

            method, path, protocol = parts

            # Extract the Host header to check for incorrect URL formats
            host = None
            for line in request_lines:
                if line.lower().startswith('host:'):
                    host = line[5:].strip()
                    break

            # Function to send a redirect response
            def send_redirect(redirect_url):
                add_log(f"Redirecting to correct URL format: {redirect_url}")

                # Prepare redirect response
                redirect_response = f"Redirecting to {redirect_url}".encode('utf-8')
                content_length = len(redirect_response)

                # Prepare headers with strict HTTP/1.1 formatting for redirect
                redirect_headers = [
                    b'HTTP/1.1 302 Found',
                    b'Server: MicroPython/1.0',
                    b'Content-Type: text/plain; charset=utf-8',
                    f'Location: {redirect_url}'.encode('utf-8'),
                    b'Cache-Control: no-cache, no-store, must-revalidate',
                    b'Pragma: no-cache',
                    b'Expires: 0',
                    b'Connection: close',
                    f'Content-Length: {content_length}'.encode('utf-8')
                ]

                # Join headers with proper CRLF
                header_bytes = b'\r\n'.join(redirect_headers) + b'\r\n\r\n'

                try:
                    # Send headers and body in a single send operation if possible
                    client_socket.sendall(header_bytes + redirect_response)
                    add_log(f"Sent redirect response in one operation")
                except AttributeError:
                    # If sendall is not available, fall back to separate sends
                    client_socket.send(header_bytes)
                    client_socket.send(redirect_response)
                    add_log(f"Sent redirect response in two operations")

            # Check for incorrect URL formats like "www.192.168.x.x"
            if host and host.startswith('www.') and any(c.isdigit() for c in host):
                add_log(f"Detected incorrect URL format with 'www.' prefix before IP address: {host}")

                # Extract the correct IP address (remove 'www.' prefix and port if present)
                correct_host = host[4:]  # Remove 'www.'
                if ':' in correct_host:
                    correct_host = correct_host.split(':')[0]  # Remove port

                # Send a redirect to the correct URL
                redirect_url = f"http://{correct_host}"
                if path != '/':
                    redirect_url += path

                send_redirect(redirect_url)
                return

            # Check for incorrect port number (8080 instead of 80)
            elif host and ':8080' in host and WEB_SERVER_PORT == 80:
                add_log(f"Detected incorrect port number in URL: {host}")

                # Extract the correct host (remove port)
                correct_host = host.split(':')[0]

                # Send a redirect to the correct URL
                redirect_url = f"http://{correct_host}"
                if path != '/':
                    redirect_url += path

                send_redirect(redirect_url)
                return

            # Log the full request for debugging
            add_log(f"Received {method} request for {path} using {protocol}")

            # Extract headers for better debugging
            headers = {}
            for line in request_lines[1:]:
                if not line or line.isspace():
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Check if the request is from Safari
            user_agent = headers.get('user-agent', '')
            safari_browser = "Safari" in user_agent and "Chrome" not in user_agent and "Edg" not in user_agent

            if safari_browser:
                add_log(f"Safari browser detected: {user_agent}")
                add_log("Using Safari-compatible response format")
        except socket.timeout:
            add_log("Timeout while receiving request")
            return

        # Generate response
        if path == '/':
            response = generate_html()
            response_bytes = response.encode('utf-8')
            content_length = len(response_bytes)

            # Prepare headers with strict HTTP/1.1 formatting
            headers = [
                b'HTTP/1.1 200 OK',
                b'Server: MicroPython/1.0',
                b'Content-Type: text/html; charset=utf-8',
                b'Cache-Control: no-cache, no-store, must-revalidate',
                b'Pragma: no-cache',
                b'Expires: 0',
                b'Access-Control-Allow-Origin: *',  # Allow cross-origin requests
                b'X-Content-Type-Options: nosniff',  # Prevent MIME type sniffing
                b'Connection: close',
                f'Content-Length: {content_length}'.encode('utf-8')
            ]

            # Join headers with proper CRLF
            header_bytes = b'\r\n'.join(headers) + b'\r\n\r\n'

            try:
                # Send headers and body in a single send operation if possible
                client_socket.sendall(header_bytes + response_bytes)
                add_log(f"Sent HTML response in one operation, size: {content_length} bytes")
            except AttributeError:
                # If sendall is not available, fall back to separate sends
                client_socket.send(header_bytes)
                client_socket.send(response_bytes)
                add_log(f"Sent HTML response in two operations, size: {content_length} bytes")

        elif path == '/api/status':
            # API endpoint for status data (for AJAX requests)
            status_data = {
                "led_states": led_states,
                "ip_addresses": ip_addresses,
                "ethernet_status": ethernet_status,
                "log": log_buffer[-10:]  # Last 10 log entries
            }
            json_response = json.dumps(status_data)
            json_bytes = json_response.encode('utf-8')
            content_length = len(json_bytes)

            # Prepare headers with strict HTTP/1.1 formatting
            headers = [
                b'HTTP/1.1 200 OK',
                b'Server: MicroPython/1.0',
                b'Content-Type: application/json; charset=utf-8',
                b'Cache-Control: no-cache, no-store, must-revalidate',
                b'Pragma: no-cache',
                b'Expires: 0',
                b'Access-Control-Allow-Origin: *',  # Allow cross-origin requests
                b'X-Content-Type-Options: nosniff',  # Prevent MIME type sniffing
                b'Connection: close',
                f'Content-Length: {content_length}'.encode('utf-8')
            ]

            # Join headers with proper CRLF
            header_bytes = b'\r\n'.join(headers) + b'\r\n\r\n'

            try:
                # Send headers and body in a single send operation if possible
                client_socket.sendall(header_bytes + json_bytes)
                add_log(f"Sent JSON response in one operation, size: {content_length} bytes")
            except AttributeError:
                # If sendall is not available, fall back to separate sends
                client_socket.send(header_bytes)
                client_socket.send(json_bytes)
                add_log(f"Sent JSON response in two operations, size: {content_length} bytes")

        elif path == '/api/reload-template':
            # API endpoint to reload the template (useful for development)
            add_log("Reload template request received")
            reload_template()

            # Return success response
            response = json.dumps({"status": "success", "message": "Template reloaded", "path": template_cache["path"]})
            response_bytes = response.encode('utf-8')
            content_length = len(response_bytes)

            # Prepare headers with strict HTTP/1.1 formatting
            headers = [
                b'HTTP/1.1 200 OK',
                b'Server: MicroPython/1.0',
                b'Content-Type: application/json; charset=utf-8',
                b'Cache-Control: no-cache, no-store, must-revalidate',
                b'Pragma: no-cache',
                b'Expires: 0',
                b'Access-Control-Allow-Origin: *',  # Allow cross-origin requests
                b'X-Content-Type-Options: nosniff',  # Prevent MIME type sniffing
                b'Connection: close',
                f'Content-Length: {content_length}'.encode('utf-8')
            ]

            # Join headers with proper CRLF
            header_bytes = b'\r\n'.join(headers) + b'\r\n\r\n'

            try:
                # Send headers and body in a single send operation if possible
                client_socket.sendall(header_bytes + response_bytes)
                add_log(f"Sent reload template response in one operation, size: {content_length} bytes")
            except AttributeError:
                # If sendall is not available, fall back to separate sends
                client_socket.send(header_bytes)
                client_socket.send(response_bytes)
                add_log(f"Sent reload template response in two operations, size: {content_length} bytes")

        else:
            # 404 Not Found
            not_found_message = b'404 Not Found'
            content_length = len(not_found_message)

            # Prepare headers with strict HTTP/1.1 formatting
            headers = [
                b'HTTP/1.1 404 Not Found',
                b'Server: MicroPython/1.0',
                b'Content-Type: text/plain; charset=utf-8',
                b'Cache-Control: no-cache, no-store, must-revalidate',
                b'Pragma: no-cache',
                b'Expires: 0',
                b'Access-Control-Allow-Origin: *',  # Allow cross-origin requests
                b'X-Content-Type-Options: nosniff',  # Prevent MIME type sniffing
                b'Connection: close',
                f'Content-Length: {content_length}'.encode('utf-8')
            ]

            # Join headers with proper CRLF
            header_bytes = b'\r\n'.join(headers) + b'\r\n\r\n'

            try:
                # Send headers and body in a single send operation if possible
                client_socket.sendall(header_bytes + not_found_message)
                add_log(f"Sent 404 response in one operation for path: {path}")
            except AttributeError:
                # If sendall is not available, fall back to separate sends
                client_socket.send(header_bytes)
                client_socket.send(not_found_message)
                add_log(f"Sent 404 response in two operations for path: {path}")
    except Exception as e:
        add_log(f"Error handling request: {e}")
    finally:
        client_socket.close()

# Start the web server
def start_server():
    add_log("Starting web interface server...")

    # Create socket with Pico 2 W optimized configuration
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Set optimized socket buffer sizes for Pico 2 W
        try:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFER_SIZE)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFER_SIZE)
            add_log(f"Socket buffers set to {SOCKET_BUFFER_SIZE} bytes")
        except OSError:
            add_log("Socket buffer size setting not supported, using defaults")

        # Set optimized timeout for Pico 2 W
        server_socket.settimeout(REQUEST_TIMEOUT)

        # Try to set additional socket options (may not be supported on all MicroPython builds)
        try:
            # Disable Nagle's algorithm for better responsiveness
            server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            add_log("TCP_NODELAY enabled")
        except (OSError, AttributeError):
            add_log("TCP_NODELAY not supported, continuing without it")

        try:
            # Keep connections alive
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            add_log("SO_KEEPALIVE enabled")
        except (OSError, AttributeError):
            add_log("SO_KEEPALIVE not supported, continuing without it")

        add_log("Socket created successfully with Pico 2 W optimized configuration")
    except Exception as e:
        add_log(f"Error creating socket: {e}")
        return

    try:
        # Bind to all interfaces with improved error handling
        max_bind_attempts = 3
        bind_attempt = 0
        bind_success = False

        while not bind_success and bind_attempt < max_bind_attempts:
            bind_attempt += 1
            try:
                # Try to bind to all interfaces
                server_socket.bind(('0.0.0.0', WEB_SERVER_PORT))
                add_log(f"Socket bound to port {WEB_SERVER_PORT} on attempt {bind_attempt}/{max_bind_attempts}")
                bind_success = True
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    add_log(f"Port {WEB_SERVER_PORT} is already in use. Attempt {bind_attempt}/{max_bind_attempts}")
                    if bind_attempt < max_bind_attempts:
                        add_log(f"Waiting before retry...")
                        # Close and recreate socket
                        server_socket.close()
                        time.sleep(2 * bind_attempt)  # Increasing wait time with each attempt
                        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    else:
                        add_log(f"Failed to bind after {max_bind_attempts} attempts")
                        raise
                else:
                    add_log(f"Error binding to port {WEB_SERVER_PORT}: {e}")
                    raise

        if not bind_success:
            add_log("Could not bind to port, exiting server")
            return

        # Start listening with optimized backlog for Pico 2 W
        server_socket.listen(MAX_CONNECTIONS)  # Optimized for memory constraints
        add_log(f"Web server running on port {WEB_SERVER_PORT}")
        add_log(f"Access the web interface at http://[device-ip]")
        add_log("Web interface running on standard HTTP port 80")

        # Log all available IP addresses for convenience
        add_log(f"WiFi IP: {ip_addresses['wifi']}")
        add_log(f"Full URL: http://{ip_addresses['wifi']}")

        # Variables for periodic memory management
        last_gc_time = time.time()
        gc_interval = 60  # Run garbage collection every 60 seconds
        connection_count = 0

        while True:
            try:
                # Accept connections
                client_socket, addr = server_socket.accept()
                connection_count += 1
                add_log(f"Connection #{connection_count} from {addr[0]}:{addr[1]}")

                # Handle the request in a try-except block
                try:
                    handle_request(client_socket)
                except Exception as e:
                    add_log(f"Error handling request from {addr[0]}:{addr[1]}: {e}")
                    try:
                        # Try to send an error response
                        error_message = b'Internal server error'
                        content_length = len(error_message)

                        # Prepare headers with strict HTTP/1.1 formatting
                        headers = [
                            b'HTTP/1.1 500 Internal Server Error',
                            b'Server: MicroPython/1.0',
                            b'Content-Type: text/plain; charset=utf-8',
                            b'Cache-Control: no-cache, no-store, must-revalidate',
                            b'Pragma: no-cache',
                            b'Expires: 0',
                            b'Access-Control-Allow-Origin: *',  # Allow cross-origin requests
                            b'X-Content-Type-Options: nosniff',  # Prevent MIME type sniffing
                            b'Connection: close',
                            f'Content-Length: {content_length}'.encode('utf-8')
                        ]

                        # Join headers with proper CRLF
                        header_bytes = b'\r\n'.join(headers) + b'\r\n\r\n'

                        try:
                            # Send headers and body in a single send operation if possible
                            client_socket.sendall(header_bytes + error_message)
                            add_log("Sent 500 error response in one operation")
                        except AttributeError:
                            # If sendall is not available, fall back to separate sends
                            client_socket.send(header_bytes)
                            client_socket.send(error_message)
                            add_log("Sent 500 error response in two operations")
                    except:
                        # Ignore errors when sending error response
                        pass
                    finally:
                        client_socket.close()

                # Periodic garbage collection for memory optimization
                current_time = time.time()
                if current_time - last_gc_time > gc_interval:
                    last_gc_time = current_time
                    gc.collect()
                    add_log(f"Memory cleanup: {gc.mem_free()} bytes free after {connection_count} connections")
            except socket.timeout:
                # This is normal, just continue
                continue
            except Exception as e:
                add_log(f"Error accepting connection: {e}")

    except Exception as e:
        add_log(f"Server error: {e}")
    finally:
        server_socket.close()
        add_log("Web server stopped")

# Main function to be called from main.py
def run_web_interface(wifi_ip=None, ethernet_ip=None, hue_bridge_ip=None):
    # Update IP addresses
    update_ip_addresses(wifi_ip, ethernet_ip, hue_bridge_ip)

    # Start the web server
    start_server()

# If this file is run directly, start the server
if __name__ == "__main__":
    add_log("Web interface started in standalone mode")
    run_web_interface()
