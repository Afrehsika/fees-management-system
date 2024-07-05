import os
import threading
import webview
from waitress import serve
from whitenoise import WhiteNoise
from config.wsgi import application  # Ensure this path is correct

application = WhiteNoise(application, root=os.path.join(os.path.dirname(__file__), 'staticfiles'))

def start_server():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Ensure this path is correct
    try:
        serve(application, host='127.0.0.1', port=8000)
    except Exception as e:
        print(f"Failed to start server: {e}")


if __name__ == '__main__':
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    # Wait briefly to ensure the server has time to start
    import time
    time.sleep(2)

    # Create and start the PyWebView window
    window = webview.create_window("Financial Office Of Akrokerri College", "http://127.0.0.1:8000", width=800, height=600)
    webview.start()
