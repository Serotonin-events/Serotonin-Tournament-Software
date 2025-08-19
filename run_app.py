# run_app.py
import webview
import threading
from app import app # Imports your existing Flask app

def start_flask():
    """Starts the Flask server in a separate thread."""
    # Use host='127.0.0.1' to ensure it's only accessible locally
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    # Start the Flask server in the background
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create and start the pywebview window with the new title
    webview.create_window(
        'Serotonin Tournament Software', 
        'http://127.0.0.1:5000',
        width=1280,
        height=800
    )
    webview.start()
