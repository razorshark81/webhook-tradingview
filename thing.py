from flask import Flask, request, jsonify, render_template, Response
import json
import logging
import sys
from datetime import datetime
from queue import Queue
import threading

# Set up logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradingview_webhook.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)

# Queue to store alerts for SSE
alert_queue = Queue()

# Webhook endpoint
@app.route('/webhook', methods=['POST'])
def tradingview_webhook():
    try:
        logging.info("Webhook request received")
        print("=== Webhook Triggered ===")

        data = request.get_json(force=True)
        if not data:
            logging.error("No JSON data received")
            print("Error: No JSON data received")
            return jsonify({"status": "error", "message": "No data received"}), 400

        raw_data_str = json.dumps(data, indent=2)
        logging.info(f"Received alert: {raw_data_str}")
        print(f"Raw Alert Data:\n{raw_data_str}")

        processed_alert = process_alert(data)
        logging.info(f"Processed alert: {processed_alert}")
        print(f"Processed Alert: {processed_alert}")

        # Add alert to queue for SSE
        alert_queue.put(processed_alert)

        return jsonify({"status": "success", "message": "Alert received"}), 200

    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        logging.error(error_msg)
        print(error_msg)
        alert_queue.put({"Error": str(e)})
        return jsonify({"status": "error", "message": str(e)}), 500

def process_alert(data):
    try:
        symbol = data.get('symbol', 'N/A')
        price = data.get('price', None)
        action = data.get('action', 'N/A')
        timestamp = data.get('time', datetime.now().isoformat())

        alert_details = {
            "Symbol": symbol,
            "Price": price,
            "Action": action,
            "Timestamp": timestamp
        }

        logging.info(f"Processed - Symbol: {symbol}, Price: {price}, Action: {action}")
        if action == 'buy':
            execute_buy_order(symbol, price)
        elif action == 'sell':
            execute_sell_order(symbol, price)

        return alert_details

    except Exception as e:
        error_msg = f"Error in process_alert: {str(e)}"
        logging.error(error_msg)
        print(error_msg)
        return {"Error": str(e)}

def execute_buy_order(symbol, price):
    msg = f"Executing BUY order for {symbol} at {price}"
    logging.info(msg)
    print(msg)

def execute_sell_order(symbol, price):
    msg = f"Executing SELL order for {symbol} at {price}"
    logging.info(msg)
    print(msg)

# SSE endpoint for real-time updates
@app.route('/alerts')
def stream_alerts():
    def event_stream():
        while True:
            try:
                alert = alert_queue.get()
                alert_str = f"[{alert['Timestamp']}] {alert.get('Action', 'N/A')} - {alert.get('Symbol', 'N/A')} @ {alert.get('Price', 'N/A')}"
                yield f"data: {json.dumps({'message': alert_str})}\n\n"
            except:
                yield "data: {}\n\n"
                threading.Event().wait(0.1)

    return Response(event_stream(), mimetype="text/event-stream")

# Main web UI
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("Starting TradingView Webhook Server...")
    logging.info("Server started")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)