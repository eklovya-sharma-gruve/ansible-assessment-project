# Ansible Automation Platform — Low-Level Design (LLD)

**Customer:** Northwind
**Generated:** 2026-08-03T17:45:58Z (UTC)
**Source platform:** http://127.0.0.1:8113  ·  **API flavour:** gateway

> Read-only extraction. Paste the relevant sections into the technical assessment report's environment / current-state architecture.

---

## 0. Automation Maturity Scorecard

**Overall maturity index: 2.89 / 5**

| # | Pillar | Score | Basis |
|---|---|---|---|
| 1 | Infrastructure & Architecture | 5 / 5 | api |
| 2 | Automation Coverage | 1 / 5 | api |
| 3 | Content Management | 3 / 5 | api |
| 4 | Security & Compliance | 4 / 5 | api |
| 5 | CI/CD & GitOps Integration | 3 / 5 | api |
| 6 | Event-Driven Automation | 1 / 5 | api |
| 7 | AI / Reasoning Readiness | 2 / 5 | survey |
| 8 | Skills & Governance | 2 / 5 | survey |
| 9 | Licensing & Cost | 5 / 5 | api |

_Basis: **api** = derived from platform telemetry · **mixed** = telemetry + Git inspection · **survey** = SA judgement. Scores are a starting point; the SA may override any pillar in the report with narrative justification._

---

## 1. Platform Infrastructure

| Attribute | Value |
|---|---|
| AAP / controller version | 4.6.7 |
| Controller HA | Yes |
| Total instances | 4 |
| Automation mesh present | Yes |
| Execution environments | 2 |

### 1.1 Instances (control plane topology)

| Hostname | Node type | State | Enabled | Capacity | CPU | Memory |
|---|---|---|---|---|---|---|
| aap-ctrl-1 | control | ready | True | 148 | 8 | 32.0 GB |
| aap-ctrl-2 | control | ready | True | 148 | 8 | 32.0 GB |
| aap-exec-1 | execution | ready | True | 296 | 16 | 64.0 GB |
| aap-hop-1 | hop | ready | True | 0 | 4 | 8.0 GB |

### 1.2 Instance groups

| Name | Container group | Min instances | Instance % | Max concurrent jobs | Max forks |
|---|---|---|---|---|---|
| controlplane | False | 2 | 100 | 0 | 0 |
| default | False | 1 | 100 | 0 | 0 |
| ocp-ee | True | 0 | 0 | 50 | 200 |

### 1.3 Execution environments

| Name | Image | Pull policy |
|---|---|---|
| Default execution environment | `registry.redhat.io/ansible-automation-platform-25/ee-supported-rhel9:latest` | missing |
| Gruve custom EE (network) | `quay.io/gruve/ee-network:1.4` | always |

---

## 2. Access & RBAC

| Attribute | Value |
|---|---|
| Organizations | 2 |
| Teams | 3 |
| Users | 16 |
| Superusers | 1 |
| System auditors | 1 |
| Credentials (count) | 19 |
| External secret backends | HashiCorp Vault Secret Lookup |

### 2.1 Organizations

| Name | Description | Max hosts |
|---|---|---|
| Default | Default org | 0 |
| Infrastructure | Infra automation | 2000 |

---

## 3. Content

| Attribute | Value |
|---|---|
| Projects | 4 |
| Git-backed projects | 3 |
| Manual (non-SCM) projects | 1 |
| Inventories | 3 |
| Total managed hosts | 980 |
| Private hub collections | 2 |

### 3.1 Projects (source of automation content)

| Name | SCM type | URL | Branch | Update on launch | Status |
|---|---|---|---|---|---|
| infra-playbooks | git | https://git.example.com/infra/playbooks.git | main | True | successful |
| network-automation | git | https://git.example.com/net/automation.git | main | True | successful |
| security-baselines | git | https://git.example.com/sec/baselines.git | prod | False | successful |
| legacy-scripts | manual | - | - | False | successful |

### 3.2 Inventories

| Name | Kind | Hosts | Groups | Has sources |
|---|---|---|---|---|
| Production | static | 612 | 24 | True |
| Non-Prod | static | 228 | 12 | True |
| Network Devices (smart) | smart | 140 | 0 | False |

**Inventory source types in use:** vmware, ec2

---

## 4. Automation Assets

| Attribute | Value |
|---|---|
| Job templates | 5 |
| Workflow job templates | 1 |
| Schedules | 2 |
| Webhook-enabled templates | 1 |

### 4.1 Job templates

| Name | Type | Playbook | Forks | Webhook | Survey |
|---|---|---|---|---|---|
| RHEL Patch - Prod | run | `patch.yml` | 20 | - | True |
| Provision VM (vSphere) | run | `provision.yml` | 10 | - | True |
| Network Backup | run | `net_backup.yml` | 25 | - | False |
| App Deploy (CI-triggered) | run | `deploy.yml` | 5 | github | False |
| CIS Hardening | run | `cis.yml` | 15 | - | True |

### 4.2 Schedules

| Name | Enabled | Recurrence (rrule) |
|---|---|---|
| Nightly patch window | True | `DTSTART:20250101T020000Z RRULE:FREQ=DAILY;INTERVAL=1` |
| Weekly network backup | True | `DTSTART:20250105T030000Z RRULE:FREQ=WEEKLY;BYDAY=SU` |

**Recent job launch mix:** manual=120, scheduled=55, workflow=15, webhook=10
**Notification integrations:** slack, webhook

---

## 5. Event-Driven Automation (EDA)

| Attribute | Value |
|---|---|
| EDA reachable | Yes |
| Rulebook activations | 0 |
| Running activations | 0 |
| Rulebooks | 0 |
| EDA projects | 0 |
| Decision environments | 0 |

_No EDA activations detected — event-driven automation not yet adopted (Track 02 opportunity)._

---

## 6. Subscription & Entitlement

| Attribute | Value |
|---|---|
| License type | enterprise |
| Subscription | AAP - 1000 Managed Nodes |
| Entitled managed nodes | 1000 |
| Currently consumed | 980 |
| Utilization | 98% |
| Compliant | Yes |
| Days remaining | 100 |

---

## 7. Job Execution Analytics

_Derived from the 200 most recent job runs — feeds Pillar 2 (toil), Pillar 6 (MTTR baseline), and the ROI model._

| Metric | Value |
|---|---|
| Jobs analysed | 200 |
| Success rate | 90% |
| Failure rate | 10% |
| Avg. job duration | 152.4 s |
| Longest job | 320.5 s |

**Busiest templates (run frequency — automation hot-spots):**
- RHEL Patch - Prod — 90 runs
- Network Backup — 60 runs
- CIS Hardening — 30 runs
- Provision VM (vSphere) — 14 runs
- App Deploy (CI-triggered) — 6 runs

**Templates with failures (closed-loop remediation candidates):**
- Provision VM (vSphere) — 14 failures
- App Deploy (CI-triggered) — 6 failures

---

## 8. RBAC Depth

| Metric | Value |
|---|---|
| Role definitions | 6 |
| Admin-type role assignments | 4 |
| Execute-type role assignments | 1 |
| Templates sampled for access | 5 |
| Total access entries (sampled) | 15 |
| Separation-of-duties signal | Present |


---

## 10. Survey-Based Signals (SA input — not machine-derived)

**Pillar 7 · AI / Reasoning Readiness** (score 2/5)
- Leadership stance: cautious
- Required control level: full_hitl
- Audit reconstruction: partial
- API/tool surface exposed: False

**Pillar 8 · Skills & Governance** (score 2/5)
- Ownership model: siloed
- Skill distribution: few_experts
- CoE status: aspirational
- Change process: informal
- Cultural trust: mixed


---

_Generated by the Gruve AAP LLD Extractor · Gruve Confidential · read-only extraction._
