# Dockerfile Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix Hadolint DL3008 warnings by pinning apt-get package versions in `deploy/Dockerfile`.

**Architecture:** Update multi-stage Dockerfile to use version patterns for Debian packages, ensuring reproducibility while allowing for minor security updates.

**Tech Stack:** Docker, Debian (Bookworm), Hadolint.

---

### Task 1: Package Version Discovery

**Files:**
- None (Diagnostic)

- [ ] **Step 1: Discover exact versions from base image**
Run: `docker run --rm python:3.11-slim apt-cache policy build-essential libpq-dev gcc libsndfile1 ffmpeg curl libpq5`
Expected: List of available versions in the Bookworm repository.

- [ ] **Step 2: Confirm version patterns**
Compare discovery results with the patterns in the spec (`12.9`, `15.*`, etc.) and adjust if necessary.

### Task 2: Implement Hardening in Dockerfile

**Files:**
- Modify: `deploy/Dockerfile`

- [ ] **Step 1: Update Builder Stage (Line 13)**

```dockerfile
# BEFORE
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gcc libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*

# AFTER
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    libpq-dev=15.* \
    gcc=4:12.* \
    libsndfile1=1.2.* \
    ffmpeg=7:5.* \
    && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 2: Update Runtime Stage (Line 22)**

```dockerfile
# BEFORE
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl libsndfile1 ffmpeg && rm -rf /var/lib/apt/lists/*

# AFTER
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=15.* \
    curl=7.* \
    libsndfile1=1.2.* \
    ffmpeg=7:5.* \
    && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 3: Commit**

```bash
git add deploy/Dockerfile
git commit -m "feat(security): pin apt package versions in Dockerfile to satisfy DL3008"
```

### Task 3: Validation

- [ ] **Step 1: Run Hadolint**
Run: `hadolint deploy/Dockerfile`
Expected: No DL3008 warnings.

- [ ] **Step 2: Verify Build**
Run: `docker build -f deploy/Dockerfile .` (or at least the builder stage to save time)
Expected: `Successfully built ...`
