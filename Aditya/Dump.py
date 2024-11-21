from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Request latency', ['endpoint'])

@app.route('/')
def index():
    REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
    with REQUEST_LATENCY.labels(endpoint='/').time():
        return jsonify(message="Welcome to the Web Server!")

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
