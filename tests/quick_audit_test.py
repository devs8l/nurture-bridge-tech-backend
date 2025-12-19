"""
Quick test to verify audit logging is working
Run this in the backend conda environment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_logging.audit import audit_authentication

print("Testing audit logging...")
print(f"Current directory: {os.getcwd()}")

# Trigger a test audit event
audit_authentication(
    actor="user:test_user",
    success=False,
    email="test@example.com",
    reason="testing_audit_log"
)

print("\n✅ Audit event triggered!")
print("Check: logs/audit.log")

# Check if file was created
audit_log_path = "logs/audit.log"
if os.path.exists(audit_log_path):
    print(f"\n✅ Audit log file created!")
    with open(audit_log_path, 'r') as f:
        content = f.read()
    print(f"\nContent:\n{content}")
else:
    print(f"\n❌ Audit log file NOT created at {audit_log_path}")
    print("This might be a permissions or configuration issue.")
