from flask import Flask, request, jsonify
import json
import os
import datetime

app = Flask(__name__)

@app.route('/api/webhook/reply', methods=['POST'])
def debug_webhook():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"n8n_payload_{timestamp}.json"
    
    try:
        data = request.get_json(force=True, silent=True) or {}
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"\n✅ Received webhook! Payload saved to: {filename}")
        print(f"Keys received: {list(data.keys())}")
        
        fields_to_check = ['message', 'body', 'text', 'html', 'plainText', 'content']
        for field in fields_to_check:
            if field in data and isinstance(data[field], str):
                print(f" - {field}: {len(data[field])} chars")
            
        return jsonify({"success": True, "message": "Captured"})
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 N8N Debug Listener running on port 5001...")
    print("----------------------------------------------------------------")
    print("1. Run 'ngrok http 5001'")
    print("2. Copy the ngrok URL (e.g. https://xxxx.ngrok.io)")
    print("3. In N8N, set webhook URL to: https://xxxx.ngrok.io/api/webhook/reply")
    print("4. Send a test email with attachments")
    print("----------------------------------------------------------------")
    app.run(port=5001, debug=True)
