#----- Edited file--------------
# incidents.py

TICKETS = [

    # ── TASK 1: Severity Classification ───────────────────────────────────────

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

    # ── TASK 2: Root Cause Classification ─────────────────────────────────────

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

    # ── TASK 3: Recommended Action ────────────────────────────────────────────

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

    # ── TASK 1: Severity (Ambiguous + Edge) ─────────────────────────────

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

    # ── TASK 2: Root Cause (Confusing Signals) ───────────────────────────

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

    # ── TASK 3: Action (Ambiguous Decisions) ─────────────────────────────

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

    # ── HARD CASES (REAL THINKING) ──────────────────────────────────────

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