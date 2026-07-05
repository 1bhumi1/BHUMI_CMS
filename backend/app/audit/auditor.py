import logging
import os
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure rotating file logger for audits
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Avoid adding handlers multiple times if reloaded
if not audit_logger.handlers:
    handler = RotatingFileHandler(
        "logs/audit.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8"
    )
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)

def log_audit_event(
    event_type: str,
    action: str,
    status: str,
    ip_address: Optional[str],
    user_agent: Optional[str],
    current_user: Optional[Any] = None,
    actor_id: Optional[int] = None,
    actor_code: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a structured audit event to the JSON audit file.
    """
    _actor_id = actor_id
    _actor_code = actor_code
    
    if current_user:
        _actor_id = getattr(current_user, "id", None)
        _actor_code = getattr(current_user, "computer_code", None)

    _details = details or {}
    
    # Track impersonation in audit log
    if current_user and getattr(current_user, "is_impersonated", False):
        _details["is_impersonated"] = True
        _details["impersonator_user_id"] = getattr(current_user, "actor_user_id", None)
        _details["impersonator_role"] = getattr(current_user, "actor_role", None)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "actor_id": _actor_id,
        "actor_computer_code": _actor_code,
        "action": action,
        "status": status,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": _details
    }
    audit_logger.info(json.dumps(event))
