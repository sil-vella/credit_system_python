from prometheus_client import Counter, Histogram, Gauge
from prometheus_flask_exporter import PrometheusMetrics
from flask import Flask

# Initialize metrics with a custom prefix to avoid conflicts
metrics = PrometheusMetrics.for_app_factory(app_name="credit_system")

# Custom metrics with more specific names
credit_transactions_counter = Counter(
    'credit_system_transaction_operations_total',
    'Total number of credit transaction operations',
    ['operation_type', 'status']
)

user_credit_balance = Gauge(
    'credit_system_user_balance_current',
    'Current credit balance for users',
    ['user_id']
)

transaction_processing_duration = Histogram(
    'credit_system_transaction_processing_seconds',
    'Duration of credit transaction processing',
    ['operation_type']
)

def init_metrics(app: Flask):
    """Initialize metrics for the Flask application."""
    metrics.init_app(app)
    
    # Register custom metrics
    metrics.register_default(
        credit_transactions_counter,
        user_credit_balance,
        transaction_processing_duration
    )
    
    return metrics 