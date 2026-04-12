#----- Edited file--------------
# incidents.py

TICKETS = [

    # TASK 1: Severity Classification

    {
        "incident_id": "INC-001",
        "task_type": "task1",
        "alert_text": "[CRITICAL] Payment service returning HTTP 503. Error rate: 94%. Affected users: ~120,000. Revenue impact confirmed.",
        "context": {
            "service": "payment-service",
            "error_rate_pct": 94,
            "affected_users": 120000,
            "region": "us-east-1",
            "last_deploy": "2h ago",
            "on_call_notified": True
        },
        "ground_truth": {"severity": "SEV1"}
    },
    {
        "incident_id": "INC-002",
        "task_type": "task1",
        "alert_text": "[WARNING] Checkout latency elevated. p99 response time: 4800ms (threshold: 2000ms). 18% of requests timing out.",
        "context": {
            "service": "checkout-service",
            "p99_latency_ms": 4800,
            "timeout_rate_pct": 18,
            "db_connections": "82/100",
            "region": "eu-west-1"
        },
        "ground_truth": {"severity": "SEV2"}
    },
    {
        "incident_id": "INC-003",
        "task_type": "task1",
        "alert_text": "[INFO] Admin dashboard CSS assets returning 404. Static file path misconfigured after deploy.",
        "context": {
            "service": "admin-ui",
            "affected_users": "internal only",
            "error_type": "404 on /static/main.css",
            "last_deploy": "30m ago",
            "user_impact": "cosmetic"
        },
        "ground_truth": {"severity": "SEV3"}
    },
    {
        "incident_id": "INC-004",
        "task_type": "task1",
        "alert_text": "[CRITICAL] Auth service down. All login attempts failing with 500. SSO token validation endpoint unreachable.",
        "context": {
            "service": "auth-service",
            "http_500_rate": "100%",
            "affected_flows": ["login", "token_refresh", "SSO"],
            "pod_status": "CrashLoopBackOff",
            "region": "global"
        },
        "ground_truth": {"severity": "SEV1"}
    },
    {
        "incident_id": "INC-005",
        "task_type": "task1",
        "alert_text": "[WARNING] Notification service email queue backlog growing. 14,000 emails pending. Delivery delay: ~22 minutes.",
        "context": {
            "service": "notification-service",
            "queue_backlog": 14000,
            "avg_delay_min": 22,
            "consumer_lag": "high",
            "revenue_impact": False
        },
        "ground_truth": {"severity": "SEV2"}
    },

    # TASK 2: Root Cause Classification

    {
        "incident_id": "INC-006",
        "task_type": "task2",
        "alert_text": "[CRITICAL] PostgreSQL replica lag: 94 seconds. Write queries spilling to disk. Connection pool exhausted on primary.",
        "context": {
            "db": "postgres-primary",
            "replica_lag_sec": 94,
            "connection_pool": "500/500",
            "disk_spill": True,
            "slow_query_count": 312
        },
        "ground_truth": {"root_cause": "DATABASE"}
    },
    {
        "incident_id": "INC-007",
        "task_type": "task2",
        "alert_text": "[CRITICAL] Packet loss 38% between us-east-1 and eu-west-1. Cross-region API calls failing. BGP route flapping detected.",
        "context": {
            "packet_loss_pct": 38,
            "affected_regions": ["us-east-1", "eu-west-1"],
            "bgp_flap": True,
            "provider": "AWS",
            "traceroute": "drops at transit hop 7"
        },
        "ground_truth": {"root_cause": "NETWORK"}
    },
    {
        "incident_id": "INC-008",
        "task_type": "task2",
        "alert_text": "[ERROR] NullPointerException in order-processing-service. Stack trace points to discount_calculator.py line 84. Deploy happened 40min ago.",
        "context": {
            "service": "order-processing",
            "exception": "NullPointerException",
            "file": "discount_calculator.py",
            "line": 84,
            "last_deploy": "40min ago",
            "git_commit": "a3f9c21"
        },
        "ground_truth": {"root_cause": "APPLICATION"}
    },
    {
        "incident_id": "INC-009",
        "task_type": "task2",
        "alert_text": "[WARNING] Stripe webhook delivery failures spiking. 503s from Stripe API. Stripe status page shows degraded payment processing.",
        "context": {
            "vendor": "Stripe",
            "webhook_failures": 840,
            "stripe_status": "degraded",
            "our_service_health": "healthy",
            "stripe_status_url": "https://status.stripe.com"
        },
        "ground_truth": {"root_cause": "THIRD_PARTY"}
    },
    {
        "incident_id": "INC-010",
        "task_type": "task2",
        "alert_text": "[CRITICAL] Node group in Kubernetes cluster terminated. 6/10 worker nodes NotReady. Pods evicted across analytics namespace.",
        "context": {
            "cluster": "prod-k8s-us-east",
            "nodes_not_ready": 6,
            "total_nodes": 10,
            "evicted_pods": 47,
            "namespace": "analytics",
            "cause": "EC2 spot interruption"
        },
        "ground_truth": {"root_cause": "INFRASTRUCTURE"}
    },

    # TASK 3: Recommended Action

    {
        "incident_id": "INC-011",
        "task_type": "task3",
        "alert_text": "[CRITICAL] API error rate jumped from 0.2% to 67% immediately after deploy v2.4.1. Rollback candidate identified.",
        "context": {
            "service": "api-gateway",
            "error_rate_before": "0.2%",
            "error_rate_after": "67%",
            "deploy_version": "v2.4.1",
            "previous_stable": "v2.4.0",
            "rollback_tested": True
        },
        "ground_truth": {"action": "ROLLBACK"}
    },
    {
        "incident_id": "INC-012",
        "task_type": "task3",
        "alert_text": "[WARNING] Search service CPU at 98%. Request queue growing. Pod autoscaler at max replicas. Flash sale traffic spike ongoing.",
        "context": {
            "service": "search-service",
            "cpu_pct": 98,
            "current_replicas": 20,
            "max_replicas_configured": 20,
            "queue_depth": 9400,
            "event": "flash sale"
        },
        "ground_truth": {"action": "SCALE_UP"}
    },
    {
        "incident_id": "INC-013",
        "task_type": "task3",
        "alert_text": "[ERROR] Worker service stuck in deadlock. Memory usage flat at 99%. Process not responding to health checks. No deploy in 6 days.",
        "context": {
            "service": "background-worker",
            "memory_pct": 99,
            "health_check": "failing",
            "last_deploy_days_ago": 6,
            "deadlock_detected": True
        },
        "ground_truth": {"action": "RESTART_SERVICE"}
    },
    {
        "incident_id": "INC-014",
        "task_type": "task3",
        "alert_text": "[CRITICAL] Primary RDS instance unresponsive. Failover to read replica not yet triggered. Data writes failing across all services.",
        "context": {
            "db": "rds-postgres-primary",
            "status": "unresponsive",
            "read_replica": "healthy",
            "auto_failover": "disabled",
            "write_failure_rate": "100%"
        },
        "ground_truth": {"action": "FAILOVER"}
    },
    {
        "incident_id": "INC-015",
        "task_type": "task3",
        "alert_text": "[WARNING] SendGrid bounce rate at 34% for transactional emails. Delivery failures concentrated on @yahoo.com domains. No infra changes.",
        "context": {
            "vendor": "SendGrid",
            "bounce_rate_pct": 34,
            "affected_domains": ["yahoo.com"],
            "our_infra_changes": False,
            "sendgrid_status": "investigating"
        },
        "ground_truth": {"action": "NOTIFY_VENDOR"}
    },
    
    {
        "incident_id": "INC-016",
        "task_type": "task1",
        "alert_text": "[INFO] Cart service intermittently failing for premium users only. Error rate: 12%.",
        "context": {
            "service": "cart-service",
            "error_rate_pct": 12,
            "affected_segment": "premium users",
            "revenue_dependency": "high",
            "region": "global"
        },
        "ground_truth": {"severity": "SEV1"}
    },

    # TASK 1: Severity (Ambiguous + Edge)

    {
        "incident_id": "INC-017",
        "task_type": "task1",
        "alert_text": "[WARNING] API latency increased to 3.2s. Error rate low (2%) but affecting checkout flow.",
        "context": {
            "service": "api-service",
            "latency_ms": 3200,
            "error_rate_pct": 2,
            "business_impact": "checkout delay"
        },
        "ground_truth": {"severity": "SEV2"}
    },
    {
        "incident_id": "INC-018",
        "task_type": "task1",
        "alert_text": "[CRITICAL] Cart service failing for 40% users. Premium users impacted more. Revenue drop observed.",
        "context": {
            "error_rate_pct": 40,
            "affected_segment": "premium",
            "revenue_impact": True
        },
        "ground_truth": {"severity": "SEV1"}
    },
    {
        "incident_id": "INC-019",
        "task_type": "task1",
        "alert_text": "[INFO] Logging service delay in ingestion pipeline. No user-facing impact.",
        "context": {
            "service": "logging",
            "delay_sec": 120,
            "user_impact": False
        },
        "ground_truth": {"severity": "SEV3"}
    },

    # TASK 2: Root Cause (Confusing Signals)

    {
        "incident_id": "INC-020",
        "task_type": "task2",
        "alert_text": "[CRITICAL] API failures with DB latency high and packet loss observed.",
        "context": {
            "db_latency_ms": 2800,
            "packet_loss_pct": 15,
            "recent_deploy": False
        },
        "ground_truth": {"root_cause": "NETWORK"}
    },
    {
        "incident_id": "INC-021",
        "task_type": "task2",
        "alert_text": "[ERROR] Service throwing timeout exceptions. No infra alerts. Code deployed 10 mins ago.",
        "context": {
            "exception": "TimeoutException",
            "deploy_time": "10m ago",
            "infra_health": "normal"
        },
        "ground_truth": {"root_cause": "APPLICATION"}
    },
    {
        "incident_id": "INC-022",
        "task_type": "task2",
        "alert_text": "[WARNING] DB CPU high and slow queries increasing gradually.",
        "context": {
            "db_cpu_pct": 92,
            "slow_queries": 210,
            "replica_lag": 5
        },
        "ground_truth": {"root_cause": "DATABASE"}
    },
    {
        "incident_id": "INC-023",
        "task_type": "task2",
        "alert_text": "[CRITICAL] Multiple pods evicted. Node memory pressure warnings.",
        "context": {
            "pods_evicted": 30,
            "node_memory_pressure": True,
            "cluster_health": "degraded"
        },
        "ground_truth": {"root_cause": "INFRASTRUCTURE"}
    },

    # TASK 3: Action (Ambiguous Decisions)

    {
        "incident_id": "INC-024",
        "task_type": "task3",
        "alert_text": "[WARNING] CPU high but traffic spike detected. Autoscaling already active.",
        "context": {
            "cpu_pct": 90,
            "traffic_spike": True,
            "autoscaling": "active"
        },
        "ground_truth": {"action": "SCALE_UP"}
    },
    {
        "incident_id": "INC-025",
        "task_type": "task3",
        "alert_text": "[ERROR] New deploy caused minor errors (5%). System stable otherwise.",
        "context": {
            "error_rate": 5,
            "deploy": "recent",
            "system_stability": "mostly stable"
        },
        "ground_truth": {"action": "INVESTIGATE"}
    },
    {
        "incident_id": "INC-026",
        "task_type": "task3",
        "alert_text": "[CRITICAL] Service stuck. No response. Health checks failing continuously.",
        "context": {
            "health_check": "failing",
            "response": "none",
            "deploy": "old"
        },
        "ground_truth": {"action": "RESTART_SERVICE"}
    },
    {
        "incident_id": "INC-027",
        "task_type": "task3",
        "alert_text": "[WARNING] Vendor API returning intermittent failures.",
        "context": {
            "vendor": "Twilio",
            "failure_rate": 18,
            "our_system": "healthy"
        },
        "ground_truth": {"action": "NOTIFY_VENDOR"}
    },
    {
        "incident_id": "INC-028",
        "task_type": "task3",
        "alert_text": "[CRITICAL] DB primary down, replica healthy.",
        "context": {
            "primary_status": "down",
            "replica": "healthy",
            "writes": "failing"
        },
        "ground_truth": {"action": "FAILOVER"}
    },

    # HARD CASES (REAL THINKING)

    {
        "incident_id": "INC-029",
        "task_type": "task3",
        "alert_text": "[WARNING] Latency increased after deploy but no errors observed.",
        "context": {
            "latency": 2500,
            "error_rate": 0,
            "deploy": "recent"
        },
        "ground_truth": {"action": "INVESTIGATE"}
    },
    {
        "incident_id": "INC-030",
        "task_type": "task2",
        "alert_text": "[CRITICAL] Failures observed. External API slow and DB connections also high.",
        "context": {
            "external_api_latency": 3000,
            "db_connections": "95%",
            "recent_deploy": False
        },
        "ground_truth": {"root_cause": "THIRD_PARTY"}
    },
    {
        "incident_id": "INC-031",
        "task_type": "task1",
        "alert_text": "[WARNING] Partial outage in recommendation engine. Affects 10% users.",
        "context": {
            "affected_users_pct": 10,
            "service": "recommendation",
            "revenue_impact": "low"
        },
        "ground_truth": {"severity": "SEV2"}
    },
    {
        "incident_id": "INC-032",
        "task_type": "task2",
        "alert_text": "[ERROR] Random crashes in service. No infra issues. No recent deploy.",
        "context": {
            "crash_logs": True,
            "infra_health": "good",
            "deploy": "none"
        },
        "ground_truth": {"root_cause": "APPLICATION"}
    },
    {
        "incident_id": "INC-033",
        "task_type": "task3",
        "alert_text": "[INFO] Minor UI glitch reported by users.",
        "context": {
            "impact": "cosmetic",
            "users_affected": 50
        },
        "ground_truth": {"action": "NO_ACTION"}
    },
    {
        "incident_id": "INC-034",
        "task_type": "task1",
        "alert_text": "[CRITICAL] Login failures spike to 70% but only in one region.",
        "context": {
            "failure_rate": 70,
            "region": "ap-south-1",
            "global_impact": False
        },
        "ground_truth": {"severity": "SEV1"}
    },
    {
        "incident_id": "INC-035",
        "task_type": "task2",
        "alert_text": "[WARNING] Increased retries and timeouts. Network stable. DB stable.",
        "context": {
            "timeouts": True,
            "network": "stable",
            "db": "stable"
        },
        "ground_truth": {"root_cause": "APPLICATION"}
    },
    {
        "incident_id": "INC-036",
        "task_type": "task3",
        "alert_text": "[WARNING] Memory leak suspected. Service degrading slowly.",
        "context": {
            "memory_growth": True,
            "crash": False,
            "impact": "gradual"
        },
        "ground_truth": {"action": "INVESTIGATE"}
    }

]


def _make_ticket(
    incident_id: str,
    task_type: str,
    alert_text: str,
    context: dict,
    expected_field: str,
    expected_value: str,
) -> dict:
    return {
        "incident_id": incident_id,
        "task_type": task_type,
        "alert_text": alert_text,
        "context": context,
        "ground_truth": {expected_field: expected_value},
    }


_EXPANDED_TASK1 = [
    ("INC-037", "[CRITICAL] Checkout API returning 502 for 58% of requests. Revenue impact confirmed during peak sale.", {"service": "checkout-api", "error_rate_pct": 58, "affected_users": 87000, "revenue_impact": True, "region": "us-west-2"}, "SEV1"),
    ("INC-038", "[WARNING] Billing dashboard latency elevated to 4200ms. 11% of invoice lookups timing out.", {"service": "billing-dashboard", "p95_latency_ms": 4200, "timeout_rate_pct": 11, "region": "eu-central-1", "revenue_impact": False}, "SEV2"),
    ("INC-039", "[INFO] Employee directory avatar placeholders rendering incorrectly. Internal only and purely cosmetic.", {"service": "employee-directory", "affected_users": "internal only", "user_impact": "cosmetic", "release": "2026.04.12"}, "SEV3"),
    ("INC-040", "[CRITICAL] Search edge returning errors globally. Error rate reached 73% across web and mobile clients.", {"service": "search-edge", "error_rate_pct": 73, "region": "global", "affected_channels": ["web", "mobile"], "on_call_notified": True}, "SEV1"),
    ("INC-041", "[WARNING] Refund worker backlog growing. 12,400 refund jobs delayed by roughly 27 minutes.", {"service": "refund-worker", "queue_backlog": 12400, "avg_delay_min": 27, "consumer_lag": "high", "revenue_impact": False}, "SEV2"),
    ("INC-042", "[INFO] Analytics dashboard legend text overlaps on one widget. No user-facing impact.", {"service": "analytics-dashboard", "impact": "cosmetic", "reported_by": "internal QA", "user_impact": False}, "SEV3"),
    ("INC-043", "[CRITICAL] Trading API rejecting 47% of high-value order placements. Revenue impact confirmed.", {"service": "trading-api", "error_rate_pct": 47, "affected_segment": "institutional", "revenue_impact": True, "region": "us-east-1"}, "SEV1"),
    ("INC-044", "[WARNING] Product catalog reads slowed to p99 3600ms. 9% of requests timing out in one region.", {"service": "catalog-read", "p99_latency_ms": 3600, "timeout_rate_pct": 9, "region": "ap-south-1", "cache_hit_rate": 61}, "SEV2"),
    ("INC-045", "[INFO] Settings page icon alignment shifted after theme update. Cosmetic only.", {"service": "settings-ui", "impact": "cosmetic", "affected_users": 430, "last_deploy": "20m ago"}, "SEV3"),
    ("INC-046", "[CRITICAL] OTP verification failures reached 41% across all regions. Login and checkout MFA both impacted.", {"service": "otp-service", "error_rate_pct": 41, "affected_flows": ["login", "checkout_mfa"], "region": "global", "on_call_notified": True}, "SEV1"),
    ("INC-047", "[WARNING] Partner sync jobs delayed by 19 minutes. Queue depth increasing but customer traffic remains steady.", {"service": "partner-sync", "queue_delay_min": 19, "queue_backlog": 3900, "revenue_impact": False, "region": "us-east-2"}, "SEV2"),
    ("INC-048", "[INFO] Internal admin export button style broke after CSS refactor. Internal only.", {"service": "admin-console", "affected_users": "internal only", "user_impact": "cosmetic", "last_deploy": "45m ago"}, "SEV3"),
    ("INC-049", "[CRITICAL] Reservation service timing out for 82% of hotel bookings. 95,000 users affected.", {"service": "reservation-service", "error_rate_pct": 82, "affected_users": 95000, "region": "eu-west-1", "revenue_impact": True}, "SEV1"),
    ("INC-050", "[WARNING] Session refresh tokens intermittently failing in one region. Error rate holding at 14%.", {"service": "session-service", "error_rate_pct": 14, "region": "sa-east-1", "affected_flows": ["token_refresh"], "revenue_impact": False}, "SEV2"),
    ("INC-051", "[INFO] Support knowledge-base thumbnails missing on article cards. No user-facing impact for customers.", {"service": "support-kb", "affected_users": "internal only", "impact": "cosmetic", "user_impact": False}, "SEV3"),
    ("INC-052", "[CRITICAL] Shipment label generation returning 500 for 52% of attempts. Revenue impact confirmed for same-day orders.", {"service": "label-service", "error_rate_pct": 52, "affected_segment": "same-day delivery", "revenue_impact": True, "region": "us-central-1"}, "SEV1"),
    ("INC-053", "[WARNING] Recommendation API latency spiked to 5100ms. 7% of requests timing out.", {"service": "recommendation-api", "p99_latency_ms": 5100, "timeout_rate_pct": 7, "region": "eu-north-1", "cache_status": "degraded"}, "SEV2"),
    ("INC-054", "[INFO] Marketing site promo banner shifted below the fold after a CSS tweak. Cosmetic only.", {"service": "marketing-site", "impact": "cosmetic", "last_deploy": "15m ago", "user_impact": "cosmetic"}, "SEV3"),
    ("INC-055", "[CRITICAL] Payroll export API failing for 100% of scheduled runs. Finance operations blocked.", {"service": "payroll-export", "http_500_rate": "100%", "affected_users": "internal finance", "region": "us-east-1", "on_call_notified": True}, "SEV1"),
    ("INC-056", "[WARNING] Loyalty points processor lagging behind by 14 minutes. Customers see delayed balances.", {"service": "loyalty-points", "avg_delay_min": 14, "affected_users_pct": 9, "revenue_impact": False, "region": "us-west-1"}, "SEV2"),
    ("INC-057", "[INFO] Observability annotation drawer not rendering markdown bullets correctly. No user-facing impact.", {"service": "observability-ui", "impact": "cosmetic", "user_impact": False, "reported_by": "internal SRE"}, "SEV3"),
    ("INC-058", "[CRITICAL] Wallet debit flow failing for 44% of attempts worldwide. Revenue dependency is high.", {"service": "wallet-debit", "error_rate_pct": 44, "region": "global", "revenue_dependency": "high", "affected_flows": ["wallet_topup", "wallet_pay"]}, "SEV1"),
    ("INC-059", "[WARNING] Fraud-score enrichment responses slowed significantly. 15% of requests timing out.", {"service": "fraud-enrichment", "timeout_rate_pct": 15, "p99_latency_ms": 3900, "region": "eu-west-2", "revenue_impact": False}, "SEV2"),
    ("INC-060", "[INFO] CMS preview page using fallback font after stylesheet cache miss. Purely cosmetic.", {"service": "cms-preview", "impact": "cosmetic", "user_impact": "cosmetic", "last_deploy": "1h ago"}, "SEV3"),
    ("INC-061", "[CRITICAL] Invoice generation failing for 65% of enterprise accounts. Revenue impact confirmed.", {"service": "invoice-engine", "error_rate_pct": 65, "affected_segment": "enterprise", "revenue_impact": True, "region": "us-east-1"}, "SEV1"),
]

_EXPANDED_TASK2 = [
    ("INC-062", "[CRITICAL] PostgreSQL vacuum lag increasing rapidly. Connection pool pinned at 480/500 on primary.", {"db": "postgres-orders", "connection_pool": "480/500", "replica_lag_sec": 41, "slow_query_count": 122}, "DATABASE"),
    ("INC-063", "[CRITICAL] Packet loss 27% on transit link. Route instability causing inter-region request failures.", {"packet_loss_pct": 27, "route_state": "flapping", "affected_regions": ["us-east-1", "ca-central-1"], "traceroute": "drops at transit hop 5"}, "NETWORK"),
    ("INC-064", "[ERROR] Exception flood began after deploy. Stack trace points to inventory_rules.py.", {"service": "inventory-service", "exception": "IllegalStateException", "stack_trace": "inventory_rules.py:118", "last_deploy": "15m ago"}, "APPLICATION"),
    ("INC-065", "[WARNING] SendGrid webhook acknowledgements failing. Vendor status page reports degraded mail delivery.", {"vendor": "SendGrid", "webhook_failures": 540, "sendgrid_status": "degraded", "our_service_health": "healthy"}, "THIRD_PARTY"),
    ("INC-066", "[CRITICAL] Kubernetes cluster degraded. Node NotReady events triggered pod evictions in checkout namespace.", {"cluster": "prod-checkout", "nodes_not_ready": 4, "evicted_pods": 29, "namespace": "checkout", "cause": "EC2 maintenance"}, "INFRASTRUCTURE"),
    ("INC-067", "[CRITICAL] Database slow query storm detected. Write queries blocked behind lock contention on Postgres.", {"database": "customer-profile", "slow_query_count": 301, "write_queries_blocked": True, "replica_lag_sec": 19}, "DATABASE"),
    ("INC-068", "[CRITICAL] Cross-region API calls failing during route flap. Traceroute drops beyond the carrier edge.", {"cross_region_calls": "failing", "route_flap": True, "traceroute": "carrier edge timeout", "packet_loss_pct": 18}, "NETWORK"),
    ("INC-069", "[ERROR] Crash loop started immediately after deploy. Code path in tax_adapter raises a NullPointerException.", {"service": "tax-adapter", "crash_count": 37, "exception": "NullPointerException", "deploy_version": "2026.04.12.4"}, "APPLICATION"),
    ("INC-070", "[WARNING] Stripe external API returning 502s. Our workers healthy but payment confirmations delayed.", {"vendor": "Stripe", "external_api_errors": 502, "worker_health": "healthy", "webhook_queue": 220}, "THIRD_PARTY"),
    ("INC-071", "[CRITICAL] Node memory pressure spread across the analytics cluster after EC2 spot interruption.", {"cluster": "analytics-prod", "node_memory_pressure": True, "spot_interruption": True, "pods_pending": 41}, "INFRASTRUCTURE"),
    ("INC-072", "[CRITICAL] Postgres replica lag hit 88 seconds. Connection pool exhausted and disk spill rising.", {"db": "postgres-ledger", "replica_lag_sec": 88, "connection_pool": "500/500", "disk_spill": True}, "DATABASE"),
    ("INC-073", "[CRITICAL] BGP convergence instability causing packet loss on network fabric between edge POPs.", {"bgp_flap": True, "packet_loss_pct": 21, "affected_regions": ["sin", "mum"], "provider": "Equinix"}, "NETWORK"),
    ("INC-074", "[ERROR] TimeoutException rate surged after release. No infrastructure alarms fired.", {"service": "pricing-engine", "exception": "TimeoutException", "last_deploy": "8m ago", "infra_health": "normal"}, "APPLICATION"),
    ("INC-075", "[WARNING] Twilio callback deliveries failing. Vendor dashboard marked degraded for messaging webhooks.", {"vendor": "Twilio", "callback_failures": 610, "twilio_status": "degraded", "webhook_latency_ms": 2600}, "THIRD_PARTY"),
    ("INC-076", "[CRITICAL] Cluster autoscaler could not recover capacity. Multiple Node NotReady alerts remain active.", {"cluster": "media-prod", "nodes_not_ready": 5, "pod_restarts": 84, "autoscaler_state": "stalled"}, "INFRASTRUCTURE"),
    ("INC-077", "[WARNING] DATABASE CPU saturation causing slow query growth after migration batch kicked off.", {"database": "ledger-db", "db_cpu_pct": 94, "slow_query_count": 143, "migration_job": "running"}, "DATABASE"),
    ("INC-078", "[CRITICAL] Traceroute drops observed at transit hop 8. Cross-region route instability persists.", {"traceroute": "drops at transit hop 8", "packet_loss_pct": 24, "cross_region_errors": 1900, "network_team_paged": True}, "NETWORK"),
    ("INC-079", "[ERROR] Random crash reports tied to auth middleware. Stack trace repeats in the same code path.", {"service": "auth-gateway", "crash_logs": True, "stack_trace": "auth_middleware.py:52", "deploy": "none"}, "APPLICATION"),
    ("INC-080", "[WARNING] External API vendor degraded. Webhook retries growing while our services remain healthy.", {"vendor": "Mapbox", "external_api_status": "degraded", "webhook_retries": 1180, "our_service_health": "healthy"}, "THIRD_PARTY"),
    ("INC-081", "[CRITICAL] Kubernetes control plane healthy, but worker cluster showing NotReady nodes and pod evictions.", {"cluster": "streaming-prod", "nodes_not_ready": 3, "evicted_pods": 24, "namespace": "transcoding"}, "INFRASTRUCTURE"),
    ("INC-082", "[CRITICAL] Write queries spilling to disk on DATABASE primary. Slow query count jumped above 400.", {"database": "orders-db", "write_queries": "spilling", "slow_query_count": 417, "replica_lag_sec": 33}, "DATABASE"),
    ("INC-083", "[CRITICAL] Network route instability causing 31% packet loss on partner edge connectivity.", {"route_state": "unstable", "packet_loss_pct": 31, "partner_edge": "degraded", "traceroute": "loss after peering route"}, "NETWORK"),
    ("INC-084", "[ERROR] Deploy triggered exception burst in settlement service. Stack trace points to a new code branch.", {"service": "settlement-service", "exception": "ValueError", "stack_trace": "settlement_flow.py:211", "last_deploy": "12m ago"}, "APPLICATION"),
    ("INC-085", "[WARNING] Vendor outage degrading payment gateway callbacks. Stripe webhook backlog keeps climbing.", {"vendor": "Stripe", "webhook_backlog": 930, "stripe_status": "incident", "our_service_health": "healthy"}, "THIRD_PARTY"),
]

_EXPANDED_TASK3 = [
    ("INC-086", "[CRITICAL] Error rate spiked immediately after deploy. Previous stable image already validated. Rollback window open.", {"service": "checkout-api", "recent_deploy_caused": True, "previous_stable": "2026.04.10.1", "rollback_tested": True}, "ROLLBACK"),
    ("INC-087", "[WARNING] Search queue depth exploded during flash sale. CPU pinned and autoscaler already at max_replicas.", {"service": "search-aggregator", "queue_depth": 18200, "cpu_pct": 97, "max_replicas": 24, "event": "flash sale"}, "SCALE_UP"),
    ("INC-088", "[ERROR] Inventory worker deadlock detected. Process not responding and health check failing continuously.", {"service": "inventory-worker", "deadlock_detected": True, "health_check": "failing", "process_state": "not responding"}, "RESTART_SERVICE"),
    ("INC-089", "[CRITICAL] Primary database down. Read replica healthy but writes failing across all tenants.", {"db": "tenant-primary", "primary_down": True, "read_replica": "healthy", "writes_failing": True}, "FAILOVER"),
    ("INC-090", "[WARNING] Stripe vendor incident causing 429s and webhook retries. Local infra healthy.", {"vendor": "Stripe", "webhook_retries": 760, "stripe_status": "degraded", "our_system": "healthy"}, "NOTIFY_VENDOR"),
    ("INC-091", "[INFO] Minor UI glitch on profile badges after CSS tweak. Cosmetic issue only.", {"service": "profile-ui", "impact": "cosmetic", "reported_users": 27}, "NO_ACTION"),
    ("INC-092", "[WARNING] Latency and retries increased gradually without a single obvious trigger. Mixed signals across services.", {"service": "document-renderer", "latency_ms": 2400, "retry_rate_pct": 8, "synthetic_probe_status": "passing"}, "INVESTIGATE"),
    ("INC-093", "[CRITICAL] Immediately after deploy, checkout failures jumped to 61%. Previous stable release is available.", {"service": "checkout-core", "immediately_after_deploy": True, "previous_stable": "2026.04.11.2", "error_rate_pct": 61}, "ROLLBACK"),
    ("INC-094", "[WARNING] Queue backlog growing fast during traffic spike. CPU saturated and autoscaler at MAX_REPLICAS.", {"service": "feed-generator", "traffic_spike": True, "queue_depth": 9700, "cpu_pct": 95, "max_replicas": 18}, "SCALE_UP"),
    ("INC-095", "[ERROR] Recommendation worker appears stuck. No response on health check endpoint for 11 minutes.", {"service": "recommendation-worker", "stuck": True, "health_check": "failing", "last_response": "11m ago"}, "RESTART_SERVICE"),
    ("INC-096", "[CRITICAL] Primary RDS unreachable. Failover has not happened yet and writes are failing.", {"db": "orders-rds-primary", "primary_rds": "unreachable", "failover": "pending", "writes_failing": True}, "FAILOVER"),
    ("INC-097", "[WARNING] Twilio vendor API returning intermittent errors. Our retry workers remain healthy.", {"vendor": "Twilio", "api_errors_pct": 23, "retry_workers": "healthy", "callback_delay_sec": 90}, "NOTIFY_VENDOR"),
    ("INC-098", "[INFO] Minor UI glitch on internal reporting theme toggle. Cosmetic only.", {"service": "reporting-ui", "impact": "cosmetic", "affected_users": "internal only"}, "NO_ACTION"),
    ("INC-099", "[WARNING] Slow degradation observed with mixed latency and retry symptoms. No single fix stands out yet.", {"service": "export-service", "latency_ms": 2800, "retry_rate_pct": 6, "error_rate_pct": 2}, "INVESTIGATE"),
    ("INC-100", "[CRITICAL] Recent deploy caused auth failures and rollback candidate already passed smoke tests.", {"service": "auth-api", "recent_deploy_caused": True, "rollback_tested": True, "previous_stable": "2026.04.11.6"}, "ROLLBACK"),
    ("INC-101", "[WARNING] CPU at 99% with queue growth on image pipeline. Autoscaler already capped at max replicas.", {"service": "image-pipeline", "cpu_pct": 99, "queue_depth": 11100, "autoscaler": "max_replicas"}, "SCALE_UP"),
    ("INC-102", "[ERROR] Scheduler deadlock detected. Process not responding to health check and jobs are stalled.", {"service": "scheduler", "deadlock_detected": True, "health_check": "failing", "job_backlog": 4400}, "RESTART_SERVICE"),
    ("INC-103", "[CRITICAL] Read replica healthy while primary down. Writes failing and customer operations blocked.", {"db": "ledger-primary", "read_replica": "healthy", "primary_down": True, "writes_failing": True}, "FAILOVER"),
    ("INC-104", "[WARNING] SendGrid vendor degradation causing delivery failures for transactional mail.", {"vendor": "SendGrid", "delivery_failures": 1300, "sendgrid_status": "investigating", "our_infra": "healthy"}, "NOTIFY_VENDOR"),
    ("INC-105", "[INFO] Cosmetic issue on loyalty badge colors after stylesheet refresh. Minor UI glitch only.", {"service": "loyalty-ui", "impact": "cosmetic", "reported_users": 61}, "NO_ACTION"),
    ("INC-106", "[WARNING] Memory usage trending upward slowly, but service still responds. Root cause not isolated yet.", {"service": "document-cache", "memory_growth": True, "probe_status": "passing", "error_rate_pct": 1}, "INVESTIGATE"),
    ("INC-107", "[CRITICAL] Recent deploy caused 54% login failures. Previous stable artifact is ready for rollback.", {"service": "login-orchestrator", "recent_deploy_caused": True, "error_rate_pct": 54, "previous_stable": "2026.04.10.9"}, "ROLLBACK"),
    ("INC-108", "[WARNING] Traffic spike from campaign launch pushed CPU to 92%. Queue depth climbing and autoscaler at max_replicas.", {"service": "campaign-router", "traffic_spike": True, "cpu_pct": 92, "queue_depth": 8600, "max_replicas": 16}, "SCALE_UP"),
]

TICKETS.extend(
    [_make_ticket(incident_id, "task1", alert_text, context, "severity", expected_value) for incident_id, alert_text, context, expected_value in _EXPANDED_TASK1]
    + [_make_ticket(incident_id, "task2", alert_text, context, "root_cause", expected_value) for incident_id, alert_text, context, expected_value in _EXPANDED_TASK2]
    + [_make_ticket(incident_id, "task3", alert_text, context, "action", expected_value) for incident_id, alert_text, context, expected_value in _EXPANDED_TASK3]
)
