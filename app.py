import json
import os
import threading
import time
from flask import Flask, render_template, jsonify, request, send_from_directory
from main_automation import CasinoAutomation
import logging
from flask_socketio import SocketIO, emit

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Configure static image folder
app.config['IMAGE_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'Images')

# Important: Configure SocketIO with the correct path and CORS settings
socketio = SocketIO(app, 
                   cors_allowed_origins="*", 
                   path="/socket.io",  # This is the default path, but being explicit
                   async_mode='threading')  # Use threading mode for better compatibility

automation = CasinoAutomation()
automation_thread = None
status_thread = None
should_stop_status_thread = False

# Add a flag to control continuous mode
continuous_mode = False

@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html')

#Serve static images
@app.route('/static/Images/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)


@app.route('/api/stats')
def get_stats():
    """API endpoint to get current statistics."""
    try:
        stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
                
            # Calculate total clicks
            total_clicks = sum(stats.get('clicks', {}).values())
            stats['totalClicks'] = total_clicks
            
            # Ensure history is properly formatted
            if 'history' not in stats or not isinstance(stats['history'], list):
                stats['history'] = []
                
            # Get last clicked casino
            if stats.get('history') and len(stats['history']) > 0:
                stats['lastClicked'] = stats['history'][-1]
                
            #logger.info(f"Stats loaded: {stats}")
            return jsonify(stats)
        else:
            # Return empty stats if file doesn't exist
            logger.warning("Stats file not found")
            return jsonify({
                "clicks": {},
                "Screenshot": {},
                "history": [],
                "totalClicks": 0
            })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "clicks": {},
            "Screenshot": {},
            "history": [],
            "totalClicks": 0
        })


def emit_status_updates():
    """Thread function to emit status updates via WebSocket."""
    global should_stop_status_thread
    while not should_stop_status_thread:
        try:
            # Get current stats
            stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = {"clicks": {}, "history": []}
                
            # Calculate total clicks
            total_clicks = sum(stats.get('clicks', {}).values())
            stats['totalClicks'] = total_clicks
            
            # Check if automation is running
            is_running = automation_thread is not None and automation_thread.is_alive() and automation.running
            
            # Emit status update
            socketio.emit('status_update', {
                'running': is_running,
                'continuous': continuous_mode,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"Error in status update thread: {str(e)}")
        
        # Sleep for a short time before next update
        time.sleep(2)

@app.route('/api/start', methods=['POST'])
def start_automation():
    global automation_thread, status_thread, should_stop_status_thread, continuous_mode
    
    logger.info("Start automation requested")
    
    # Get continuous mode from request
    data = request.json or {}
    continuous_mode = data.get('continuous', False)
    logger.info(f"Continuous mode: {continuous_mode}")
    
    if automation_thread and automation_thread.is_alive() and automation.running:
        logger.info("Automation already running")
        return jsonify({"status": "already_running", "message": "Automation is already running"})
    
    # Reset the automation object to ensure a clean state
    automation.running = True
    logger.info("Starting automation thread")
    
    # Define a wrapper function to handle errors and continuous mode
    def run_with_error_handling():
        try:
            if continuous_mode:
                logger.info("Running in continuous mode")
                while automation.running:
                    automation.main(run_once=True)
                    if not automation.running:
                        break
                    time.sleep(5)  # Wait between runs
            else:
                logger.info("Running in single run mode")
                automation.main(run_once=True)
        except Exception as e:
            logger.error(f"Error in automation thread: {str(e)}", exc_info=True)
            automation.running = False
            socketio.emit('automation_error', {'message': str(e)})
        finally:
            logger.info("Automation thread completed")
            automation.running = False
            socketio.emit('status_update', {
                'running': False,
                'continuous': continuous_mode,
                'message': 'Automation completed'
            })
    
    # Start the automation thread
    automation_thread = threading.Thread(target=run_with_error_handling)
    automation_thread.daemon = True
    automation_thread.start()
    
    # Start the status update thread if not already running
    if status_thread is None or not status_thread.is_alive():
        should_stop_status_thread = False
        status_thread = threading.Thread(target=emit_status_updates)
        status_thread.daemon = True
        status_thread.start()
    
    logger.info("Automation thread started")
    return jsonify({
        "status": "started", 
        "message": "Automation started successfully",
        "continuous": continuous_mode
    })

@app.route('/api/stop', methods=['POST'])
def stop_automation():
    """API endpoint to stop the automation."""
    global automation_thread, continuous_mode
    
    logger.info("Stop automation requested")
    
    if not automation_thread or not automation_thread.is_alive():
        logger.info("No automation thread running")
        return jsonify({"status": "not_running", "message": "Automation is not running"})
    
    if not automation.running:
        logger.info("Automation already stopped")
        return jsonify({"status": "not_running", "message": "Automation is already stopped"})
    
    logger.info("Stopping automation")
    # Signal the automation to stop
    automation.running = False
    automation.stop()
    
    # Wait for a short time to ensure the stop signal is processed
    time.sleep(1)
    
    # Force stop if still running
    if automation_thread and automation_thread.is_alive() and automation.running:
        logger.warning("Automation did not stop gracefully, forcing stop")
        automation.running = False
        # Don't join the thread here as it might be blocked
    
    continuous_mode = False
    
    return jsonify({"status": "stopping", "message": "Automation is stopping"})

@app.route('/api/toggle_continuous', methods=['POST'])
def toggle_continuous():
    """API endpoint to toggle continuous mode."""
    global continuous_mode
    
    data = request.json or {}
    continuous_mode = data.get('continuous', not continuous_mode)
    
    return jsonify({
        "status": "success", 
        "continuous": continuous_mode,
        "message": f"Continuous mode {'enabled' if continuous_mode else 'disabled'}"
    })

@app.route('/api/status')
def get_status():
    """API endpoint to check if automation is running."""
    global automation_thread, continuous_mode
    is_running = (automation_thread is not None and 
                 automation_thread.is_alive() and 
                 automation.running)
    
    return jsonify({
        "running": is_running,
        "continuous": continuous_mode,
        "status": "running" if is_running else "stopped"
    })

@app.route('/api/reset', methods=['POST'])
def reset_stats():
    """API endpoint to reset statistics."""
    try:
        stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
        with open(stats_file, 'w') as f:
            json.dump({
                "clicks": {},
                "Screenshot": {},
                "history": []
            }, f, indent=2)
        return jsonify({"status": "success", "message": "Statistics reset successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected to WebSocket')
    # Send initial status on connection
    is_running = automation_thread is not None and automation_thread.is_alive() and automation.running
    
    # Get current stats
    try:
        stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
                
            # Calculate total clicks
            total_clicks = sum(stats.get('clicks', {}).values())
            stats['totalClicks'] = total_clicks
        else:
            stats = {"clicks": {}, "Screenshot": {}, "history": [], "totalClicks": 0}
    except Exception as e:
        logger.error(f"Error loading stats: {str(e)}")
        stats = {"clicks": {}, "Screenshot": {}, "history": [], "totalClicks": 0}
    
    emit('status_update', {
        'running': is_running,
        'continuous': continuous_mode,
        'stats': stats
    })

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected from WebSocket')

@socketio.on('request_status')
def handle_status_request():
    is_running = automation_thread is not None and automation_thread.is_alive() and automation.running
    
    # Get current stats
    try:
        stats_file = os.path.join(os.path.dirname(__file__), "data", "stats.json")
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                stats = json.load(f)
                
            # Calculate total clicks
            total_clicks = sum(stats.get('clicks', {}).values())
            stats['totalClicks'] = total_clicks
        else:
            stats = {"clicks": {}, "history": [], "totalClicks": 0}
    except Exception as e:
        logger.error(f"Error loading stats: {str(e)}")
        stats = {"clicks": {}, "history": [], "totalClicks": 0}
    
    emit('status_update', {
        'running': is_running,
        'continuous': continuous_mode,
        'stats': stats
    })

if __name__ == '__main__':
    # Ensure the data directory exists
    os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
    
    try:
        # Disable auto-reloading by setting use_reloader=False
        socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        # Handle clean shutdown
        logger.info("Shutting down...")
        should_stop_status_thread = True
        if automation_thread and automation_thread.is_alive():
            automation.running = False
            automation.stop()
            time.sleep(1)
