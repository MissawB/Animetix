# Design Spec: Dockerfile Security Hardening (Hadolint)

**Date:** 2026-06-15
**Status:** Approved
**Topic:** Resolving DL3008 warnings in `deploy/Dockerfile` via package pinning.

## 1. Purpose
The Animetix `deploy/Dockerfile` failed a Hadolint audit due to unpinned `apt-get install` commands. This spec outlines the implementation of version pinning to improve build reproducibility and security.

## 2. Constraints & Success Criteria
- **Compliance:** Clear all Hadolint `DL3008` warnings.
- **Stability:** Use version patterns (e.g., `pkg=1.2.*`) that allow minor security patches within the same major version to prevent build breakage on Debian repository updates.
- **Success Criteria:** `hadolint deploy/Dockerfile` returns 0 warnings for lines 13 and 22.

## 3. Architecture & Implementation

### 3.1 Base Image Context
The Dockerfile uses `python:3.11-slim`, which is based on Debian 12 (Bookworm). Version pins must align with Bookworm's repository.

### 3.2 Implementation Plan
Modify `deploy/Dockerfile` to update the `RUN apt-get install` commands.

#### Builder Stage (Line 13)
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    libpq-dev=15.* \
    gcc=4:12.* \
    libsndfile1=1.2.* \
    ffmpeg=7:5.* \
    && rm -rf /var/lib/apt/lists/*
```

#### Runtime Stage (Line 22)
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=15.* \
    curl=7.* \
    libsndfile1=1.2.* \
    ffmpeg=7:5.* \
    && rm -rf /var/lib/apt/lists/*
```

## 4. Testing & Validation
1. **Linting:** Run Hadolint on the modified Dockerfile.
2. **Build Verification:** Execute a local `docker build -f deploy/Dockerfile .` to ensure the version pins are valid and the build succeeds.
