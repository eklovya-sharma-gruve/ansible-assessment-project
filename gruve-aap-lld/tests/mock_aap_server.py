#!/usr/bin/env python3
"""Minimal mock of the AAP gateway API for validating the LLD playbook.
Serves realistic JSON for the endpoints the role calls. No auth enforced
(the playbook still sends the bearer header)."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

C = "/api/controller/v2"
E = "/api/eda/v1"
G = "/api/galaxy/_ui/v1"

def page(results):
    return {"count": len(results), "next": None, "previous": None, "results": results}

ROUTES = {
    f"{C}/ping/": {"version": "4.6.7", "ha": True, "instances": []},
    f"{C}/instances/": page([
        {"hostname": "aap-ctrl-1", "node_type": "control", "node_state": "ready", "enabled": True, "capacity": 148, "cpu": 8, "memory": "32.0 GB", "ip_address": "10.20.1.11"},
        {"hostname": "aap-ctrl-2", "node_type": "control", "node_state": "ready", "enabled": True, "capacity": 148, "cpu": 8, "memory": "32.0 GB", "ip_address": "10.20.1.12"},
        {"hostname": "aap-exec-1", "node_type": "execution", "node_state": "ready", "enabled": True, "capacity": 296, "cpu": 16, "memory": "64.0 GB", "ip_address": "10.20.1.21"},
        {"hostname": "aap-hop-1", "node_type": "hop", "node_state": "ready", "enabled": True, "capacity": 0, "cpu": 4, "memory": "8.0 GB", "ip_address": "10.20.2.5"},
    ]),
    f"{C}/instance_groups/": page([
        {"name": "controlplane", "is_container_group": False, "policy_instance_minimum": 2, "policy_instance_percentage": 100, "max_concurrent_jobs": 0, "max_forks": 0},
        {"name": "default", "is_container_group": False, "policy_instance_minimum": 1, "policy_instance_percentage": 100, "max_concurrent_jobs": 0, "max_forks": 0},
        {"name": "ocp-ee", "is_container_group": True, "policy_instance_minimum": 0, "policy_instance_percentage": 0, "max_concurrent_jobs": 50, "max_forks": 200},
    ]),
    f"{C}/execution_environments/": page([
        {"name": "Default execution environment", "image": "registry.redhat.io/ansible-automation-platform-25/ee-supported-rhel9:latest", "pull": "missing"},
        {"name": "Gruve custom EE (network)", "image": "quay.io/gruve/ee-network:1.4", "pull": "always"},
    ]),
    f"{C}/organizations/": page([
        {"name": "Default", "description": "Default org", "max_hosts": 0},
        {"name": "Infrastructure", "description": "Infra automation", "max_hosts": 2000},
    ]),
    f"{C}/teams/": page([
        {"name": "Platform", "summary_fields": {"organization": {"name": "Infrastructure"}}},
        {"name": "NetOps", "summary_fields": {"organization": {"name": "Infrastructure"}}},
        {"name": "SecOps", "summary_fields": {"organization": {"name": "Infrastructure"}}},
    ]),
    f"{C}/users/": page([
        {"username": "admin", "is_superuser": True, "is_system_auditor": False},
        {"username": "auditor", "is_superuser": False, "is_system_auditor": True},
    ] + [{"username": f"eng{i}", "is_superuser": False, "is_system_auditor": False} for i in range(14)]),
    f"{C}/credential_types/": page([
        {"name": "Machine", "kind": "ssh"},
        {"name": "Source Control", "kind": "scm"},
        {"name": "HashiCorp Vault Secret Lookup", "kind": "external"},
    ]),
    f"{C}/credentials/": page([{"name": f"cred{i}", "summary_fields": {"credential_type": {"name": "Machine"}}} for i in range(19)]),
    f"{C}/projects/": page([
        {"name": "infra-playbooks", "scm_type": "git", "scm_url": "https://git.example.com/infra/playbooks.git", "scm_branch": "main", "scm_refspec": "", "status": "successful", "scm_update_on_launch": True},
        {"name": "network-automation", "scm_type": "git", "scm_url": "https://git.example.com/net/automation.git", "scm_branch": "main", "scm_refspec": "", "status": "successful", "scm_update_on_launch": True},
        {"name": "security-baselines", "scm_type": "git", "scm_url": "https://git.example.com/sec/baselines.git", "scm_branch": "prod", "scm_refspec": "", "status": "successful", "scm_update_on_launch": False},
        {"name": "legacy-scripts", "scm_type": "", "scm_url": "", "scm_branch": "", "scm_refspec": "", "status": "successful", "scm_update_on_launch": False},
    ]),
    f"{C}/inventories/": page([
        {"name": "Production", "kind": "", "total_hosts": 612, "total_groups": 24, "has_inventory_sources": True},
        {"name": "Non-Prod", "kind": "", "total_hosts": 228, "total_groups": 12, "has_inventory_sources": True},
        {"name": "Network Devices (smart)", "kind": "smart", "total_hosts": 140, "total_groups": 0, "has_inventory_sources": False},
    ]),
    f"{C}/inventory_sources/": page([
        {"name": "vmware-prod", "source": "vmware"},
        {"name": "aws-prod", "source": "ec2"},
    ]),
    f"{C}/job_templates/": page([
        {"id": 1, "name": "RHEL Patch - Prod", "job_type": "run", "playbook": "patch.yml", "forks": 20, "verbosity": 0, "webhook_service": "", "survey_enabled": True, "ask_variables_on_launch": False},
        {"id": 2, "name": "Provision VM (vSphere)", "job_type": "run", "playbook": "provision.yml", "forks": 10, "verbosity": 0, "webhook_service": "", "survey_enabled": True, "ask_variables_on_launch": True},
        {"id": 3, "name": "Network Backup", "job_type": "run", "playbook": "net_backup.yml", "forks": 25, "verbosity": 0, "webhook_service": "", "survey_enabled": False, "ask_variables_on_launch": False},
        {"id": 4, "name": "App Deploy (CI-triggered)", "job_type": "run", "playbook": "deploy.yml", "forks": 5, "verbosity": 1, "webhook_service": "github", "survey_enabled": False, "ask_variables_on_launch": False},
        {"id": 5, "name": "CIS Hardening", "job_type": "run", "playbook": "cis.yml", "forks": 15, "verbosity": 0, "webhook_service": "", "survey_enabled": True, "ask_variables_on_launch": False},
    ]),
    f"{C}/workflow_job_templates/": page([
        {"name": "Full Stack Provision", "survey_enabled": True},
    ]),
    f"{C}/schedules/": page([
        {"name": "Nightly patch window", "rrule": "DTSTART:20250101T020000Z RRULE:FREQ=DAILY;INTERVAL=1", "enabled": True},
        {"name": "Weekly network backup", "rrule": "DTSTART:20250105T030000Z RRULE:FREQ=WEEKLY;BYDAY=SU", "enabled": True},
    ]),
    f"{C}/notification_templates/": page([
        {"name": "Slack ops", "notification_type": "slack"},
        {"name": "ServiceNow inc", "notification_type": "webhook"},
    ]),
    f"{C}/unified_jobs/?order_by=-finished&page_size=200": page(
        [{"launch_type": "manual"}] * 120 + [{"launch_type": "scheduled"}] * 55 +
        [{"launch_type": "workflow"}] * 15 + [{"launch_type": "webhook"}] * 10),
    f"{C}/config/": {"license_info": {
        "license_type": "enterprise", "subscription_name": "AAP - 1000 Managed Nodes",
        "instance_count": 1000, "current_instances": 980, "free_instances": 20,
        "compliant": True, "trial": False, "time_remaining": 8640000}},
    # roles (RBAC depth)
    f"{C}/roles/": page([
        {"name": "System Administrator"}, {"name": "Organization Admin"},
        {"name": "Project Admin"}, {"name": "Job Template Execute"},
        {"name": "Inventory Admin"}, {"name": "Auditor"},
    ]),
    # recent jobs for analytics (distinct from unified_jobs)
    f"{C}/jobs/?order_by=-finished&page_size=400": page(
        [{"name": "RHEL Patch - Prod", "status": "successful", "elapsed": 182.4}] * 90 +
        [{"name": "Network Backup", "status": "successful", "elapsed": 45.1}] * 60 +
        [{"name": "Provision VM (vSphere)", "status": "failed", "elapsed": too_long}
         for too_long in [320.5] * 14] +
        [{"name": "CIS Hardening", "status": "successful", "elapsed": 210.0}] * 30 +
        [{"name": "App Deploy (CI-triggered)", "status": "error", "elapsed": 95.2}] * 6),
    # EDA - not adopted yet
    f"{E}/activations/": page([]),
    f"{E}/rulebooks/": page([]),
    f"{E}/projects/": page([]),
    f"{E}/decision-environments/": page([]),
    # Hub
    f"{G}/repo/published/": page([{"name": "gruve.infra"}, {"name": "gruve.network"}]),
}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def do_GET(self):
        body = ROUTES.get(self.path)
        if body is None and "?" in self.path:
            body = ROUTES.get(self.path.split("?")[0] + "/") or ROUTES.get(self.path.split("?")[0])
        # dynamic: /job_templates/{id}/access_list/
        if body is None and "/access_list/" in self.path:
            body = page([{"username": "admin"}, {"username": "eng1"}, {"username": "eng2"}])
        if body is None:
            body = page([])  # unknown endpoint -> empty page (mirrors graceful degradation)
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8113), H).serve_forever()
