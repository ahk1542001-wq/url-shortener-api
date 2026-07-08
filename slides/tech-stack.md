---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #f8f9fa
---

# 🚀 URL Shortener API
## Tech Stack & AI Workflow
**Developer:** @ahk1542001-wq
**Project:** Vibe Coding Tour

---

# 💻 The Tech Stack

- **Backend:** FastAPI (Python) - Fast, modern, and reliable web framework.
- **Frontend:** Vanilla HTML, CSS, JavaScript.
- **Styling:** Custom "Glassmorphism" UI with dark mode support.
- **Deployment:** Render (Free Tier).

---

# 🤖 AI Agents & Skills

### **Agent:** `deploy-master`
- DevOps subagent for ensuring production readiness.
- *Capabilities:* Security scanning, automated testing, code formatting checks, and database migration checks.

### **Skill:** `pre-deploy-check`
- Automates the rigorous pre-deployment checklist.
- *Checks:* `requirements.txt` vulnerabilities, PEP8 linting, `pytest` execution, and environment variable validation.

---

# 🧠 Methodology

We utilized **Vibe Coding** and **Subagent-Driven Development**:
- Rapid prototyping using Claude.
- Isolated tasks (like Security & Deployment Audits) delegated to specialized subagents.
- Continuous deployment to Render for instant feedback.

---

# ⚡ Triggers & Commands

How we fire our AI workflows:

### **Trigger** 
Whenever we are about to push new changes to the `main` branch that will trigger an automatic deployment on Render.

### **Command**
`"Invoke the deploy-master agent and run the pre-deploy-check skill"`
