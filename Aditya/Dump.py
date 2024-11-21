{
  "dashboard": {
    "id": null,
    "title": "Web Server Performance",
    "panels": [
      {
        "type": "graph",
        "title": "HTTP Requests",
        "targets": [
          {
            "expr": "http_requests_total",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "type": "graph",
        "title": "Request Latency",
        "targets": [
          {
            "expr": "http_request_latency_seconds_bucket",
            "legendFormat": "{{endpoint}}"
          }
        ]
      }
    ]
  }
}
