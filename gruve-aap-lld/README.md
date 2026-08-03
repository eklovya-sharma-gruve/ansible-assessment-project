# Gruve AAP LLD Extractor & Maturity Scanner

A **read-only** Ansible job template that runs *on* Ansible Automation Platform and
produces the evidence base for the **Gruve AAP Assessment**. In one launch it:

1. **Extracts the low-level design (LLD)** — versions, node topology, execution
   environments, RBAC, projects, inventories, job templates, schedules, EDA, and
   subscription — into a JSON bundle plus **Markdown and HTML reports** you paste
   straight into the technical assessment report.
2. **Computes a 1–5 maturity score for all 9 assessment pillars**, each tagged with
   its evidence basis (API-derived / Git-derived / survey).
3. **Optionally inspects Git content** for quality, CI/testing evidence, and
   **plaintext secrets** (locations only — never values).
4. **Merges an SA survey** for the two pillars no API can see (AI readiness, skills).

Validated end-to-end against a mock AAP API and a real Git repo: **160 tasks, 0 failures**;
the secret scanner correctly flagged planted credentials by file + line.

---

## 1. What it maps to your assessment

The assessment defines **9 pillars / 54 discovery questions / 9 evidence sets**. This
tool covers them in three tiers. Be clear-eyed: some things are inherently human and
stay in the survey — the tool never fabricates those.

| Pillar | Coverage | What the tool derives automatically |
|---|---|---|
| 1 · Infrastructure & Architecture | **Full (API)** | version/patch, HA, controller/exec/hop topology, mesh, EE inventory |
| 2 · Automation Coverage | **High (API)** | job-template count, managed hosts, schedules, manual-vs-triggered ratio, **success/fail, run frequency, duration** |
| 3 · Content Management | **High (API+Git)** | Git-vs-manual projects, SCM URLs/branches, hub collections; **roles vs standalone, reuse/duplication, meta/ standards** (Git) |
| 4 · Security & Compliance | **High (API+Git)** | external vault detection, RBAC structure, **role defs, access-lists, separation-of-duties**; **plaintext-secret scan** (Git) |
| 5 · CI/CD & GitOps | **High (API+Git)** | Git ratio, webhook templates; **ansible-lint / yamllint / Molecule / CI / config-as-code detection** (Git) |
| 6 · Event-Driven | **Full (API)** | EDA activations, rulebooks, decision environments, running state; **failing-template remediation candidates** |
| 7 · AI / Reasoning Readiness | **Survey** | qualitative — appetite, control model, audit confidence, API surface |
| 8 · Skills & Governance | **Survey** | qualitative — ownership, CoE, change process, culture |
| 9 · Licensing & Cost | **Full (API)** | tier, entitlement vs. consumed, utilization %, compliance, days to renewal |

### What cannot be automated (stays in the survey — by design)

The tool will not invent these; they come from the SA workshop and feed the report/ROI:

- Business objectives in the customer's own words (report §2.2)
- Engineer-hours per domain, fully-loaded cost → the entire ROI model (§6)
- "Top 3–5 most painful manual tasks" (subjective)
- Leadership AI stance, required control level (Pillar 7)
- Team skill distribution, CoE maturity, cultural trust, onboarding (Pillar 8)
- Renewal/EBR **intent** (dates are visible; intent is not) (Pillar 9)
- Whether **DR failover was actually tested** (config is visible; the test is a claim)

The report and JSON bundle **label every score's basis** so the customer trusts the
machine-derived parts and the SA owns the judgement parts.

---

## 2. Outputs

Written to `lld_output_dir` (default `/tmp/gruve_lld`, or the job's isolated data dir),
and surfaced as job artifacts via `set_stats`:

| File | Purpose |
|---|---|
| `lld_bundle.json` | Machine-readable: every fact + scores + provenance + collection-error notes |
| `lld_report.md` | LLD + scorecard organized by domain — paste into the technical report |
| `lld_report.html` | Same, Gruve-branded, as a review copy |

`set_stats` also exposes AAP version, instance count, managed hosts, **maturity index**,
and output paths — visible in the job's **Artifacts** panel and usable by downstream jobs.

---

## 3. Quick start

### On AAP as a job template (the easy-run path, ~5 min)

1. **Token** — as a read-only user: *User → Tokens → Add*, scope **read**. Copy it.
2. **Project** — *Resources → Projects → Add*: SCM Git, point at this repo.
3. **Job template** — *Resources → Templates → Add*:
   - Inventory: any (runs on `localhost`, `connection: local`)
   - Project: from step 2 · Playbook: `playbooks/lld_extract.yml`
   - Execution environment: **Default execution environment** (or a git-enabled EE if
     you plan to use Git inspection — see §6)
4. **Survey** — import `jobtemplate/survey_spec.json`. It collects the token, customer
   name, API flavour, TLS flag, the Git-inspection opt-in, an optional SCM token, and an
   optional survey-file path.
5. **Launch.** On the controller, `aap_hostname` auto-resolves from `CONTROLLER_HOST`;
   you only enter the token and customer name.

> Config-as-code alternative: `jobtemplate/controller_config.yml` defines the same
> template for the `infra.aap_configuration` / `awx.awx` collections.

### From the CLI (testing)

```bash
ANSIBLE_ROLES_PATH=./roles ansible-playbook playbooks/lld_extract.yml \
  -e aap_hostname=https://aap-gateway.customer.com \
  -e aap_token=$AAP_READONLY_TOKEN \
  -e lld_customer_name="Acme Corp" \
  -e aap_api_flavour=gateway \
  -e survey_file=/path/to/survey.yml \
  -e lld_output_dir=./out
```

### Validate locally with no AAP (mock)

```bash
python3 tests/mock_aap_server.py &            # serves realistic LLD on :8113
ANSIBLE_ROLES_PATH=./roles ansible-playbook playbooks/lld_extract.yml \
  -e aap_hostname=http://127.0.0.1:8113 -e aap_token=x \
  -e aap_validate_certs=false -e lld_customer_name="Demo" -e lld_output_dir=./out
```

---

## 4. All variables

| Variable | Default | Purpose |
|---|---|---|
| `aap_hostname` | `$CONTROLLER_HOST` | Platform base URL |
| `aap_token` | — (required) | Read-only OAuth token |
| `aap_validate_certs` | `true` | TLS verification |
| `aap_api_flavour` | `gateway` | `gateway` (2.5+) or `legacy` (2.4) |
| `lld_customer_name` | `[CUSTOMER NAME]` | Report header |
| `lld_output_dir` | `/tmp/gruve_lld` | Where outputs are written |
| `collect_infrastructure` … `collect_licensing` | `true` | Core LLD domains |
| `collect_rbac_depth` | `true` | Access-lists, role assignments |
| `collect_job_analytics` | `true` | Success/fail, MTTR proxy, frequency |
| `collect_git_inspection` | **`false`** | **Opt-in** Git clone-and-inspect |
| `merge_survey` | `true` | Fold survey into the bundle |
| `compute_scoring` | `true` | Derive 1–5 pillar scores |
| `analytics_job_sample` | `400` | Recent jobs to analyse |
| `git_scm_username` / `git_scm_token` | `""` | Read-only creds for private repos |
| `git_clone_depth` | `1` | Shallow clone |
| `git_max_repos` | `25` | Safety cap |
| `git_secret_patterns` | 4 built-ins | Secret-scan regexes |
| `survey_file` | `""` | Path to `survey.yml`; blank = neutral defaults |

---

## 5. The SA survey (pillars 7 & 8 + ROI)

Copy `roles/aap_lld/templates/survey.example.yml`, fill it during the workshop, and pass
its path as `survey_file`. It carries:

- **Pillar 7** — AI readiness: leadership stance, control level, audit confidence, API surface
- **Pillar 8** — Skills: ownership model, CoE status, change process, culture, onboarding
- **Interview signals** — DR-tested claim, top manual tasks, monitoring/ITSM tools,
  remediation candidates, renewal date, expansion appetite
- **ROI baseline** — engineer cost/hr, hours per domain, MTTR, incident volume, change-failure cost

These merge into the bundle; survey-scored pillars are marked `basis: survey`.

---

## 6. Git inspection (opt-in) — what to know

The single highest-value enhancement: it closes pillars 3, 4, and 5 at once by cloning
each Git-backed project (read-only, shallow) and inspecting it. It detects roles vs.
standalone playbooks, cross-repo role duplication (copy-paste sprawl), `meta/` standards,
ansible-lint / yamllint / Molecule / CI pipelines / config-as-code, and **scans for
plaintext secrets**.

**Security posture — read before enabling:**

- **Opt-in only** (`collect_git_inspection: true`); off by default.
- Clones are **shallow and never executed** — content is read, not run.
- The secret scanner reports **file · line · pattern name only — never the secret value**.
  Vaulted lines (`!vault`) and comments are skipped.
- The workspace is deleted at the end of the run.
- Needs a **read-only SCM token** for private repos and the **`git` binary in the EE**
  (default EE has it; a minimal custom EE may not). If `git` is missing, the tool records
  a note and continues.
- This is a **bigger security-review ask** than the read-only API token — some customers
  will decline it. That's fine: everything else still runs and the affected pillars fall
  back to API-only signals.

---

## 7. Scoring — how it works

`tasks/scoring.yml` derives each pillar's 1–5 score from transparent thresholds over the
collected evidence (e.g. HA + clustered + mesh + custom EEs → Infrastructure 5; EDA in use
+ running + ≥3 rulebooks → Event-Driven 4). Pillars 7 & 8 come from the survey. Every score
carries a `basis` (`api` / `mixed` / `survey`). **Scores are a starting point** — the SA can
override any pillar in the report with narrative justification, as the battlecard rubric intends.

---

## 8. Design principles

- **Read-only & safe.** Only GET; token header is `no_log`; nothing on the platform is modified.
- **Resilient.** A missing/erroring endpoint yields an empty section plus a note in
  `meta.collection_errors` — one gap never aborts the run (proven: unreachable repos degraded cleanly).
- **Self-contained.** Custom filters ship with the role; no `json_query` / `community.general`.
- **Version-tolerant.** Configurable prefixes for AAP 2.4 → 2.6.
- **Honest.** Machine-derived vs. survey-based signals are labelled everywhere.

---

## 9. Layout

```
playbooks/lld_extract.yml               entry playbook
roles/aap_lld/
  defaults/main.yml                     connection, prefixes, toggles, git/survey config
  tasks/
    main.yml                            orchestration
    infrastructure.yml rbac.yml content.yml automation.yml event_driven.yml licensing.yml
    rbac_depth.yml                      v2: access-lists, role assignments
    job_analytics.yml                   v2: success/fail, MTTR proxy, frequency
    git_inspection.yml                  v2: opt-in Git clone-and-inspect
    survey_merge.yml                    v2: fold survey into facts
    scoring.yml                         v2: derive 1-5 pillar scores
    _fetch.yml _paginate_more.yml       paginated GET helper
  files/git_inspect.py                  Git inspector (stdlib + git binary)
  filter_plugins/gruve_filters.py       custom filters
  templates/
    lld_report.md.j2  lld_report.html.j2   reports (scorecard + LLD + v2 sections)
    survey.example.yml                  SA survey template
jobtemplate/
  survey_spec.json                      importable AAP survey
  controller_config.yml                 job-template-as-code
tests/mock_aap_server.py                local validation harness
sample_output/                          example generated reports
```

---

## 10. What I'd add next

- **Automation Analytics / Subscription Usage** pull for a real consumption *trend* (Pillar 9).
- **Notification-type classification** (ServiceNow / PagerDuty / Slack) scored into Pillar 6.
- **Auto-generate the Word technical report** from `lld_bundle.json` so §2 Environment and
  §3 Scorecard populate themselves.
