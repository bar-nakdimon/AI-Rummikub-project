# Rummikub Solver

[![CI](https://github.com/bar-nakdimon/AI-Rummikub-project/actions/workflows/ci.yml/badge.svg)](https://github.com/bar-nakdimon/AI-Rummikub-project/actions/workflows/ci.yml)
[![CD](https://github.com/bar-nakdimon/AI-Rummikub-project/actions/workflows/deploy.yml/badge.svg)](https://github.com/bar-nakdimon/AI-Rummikub-project/actions/workflows/deploy.yml)
[![Docker images](https://img.shields.io/badge/docker-ghcr.io-2496ED?logo=docker&logoColor=white)](https://github.com/bar-nakdimon?tab=packages&repo_name=AI-Rummikub-project)

An AI-powered mobile assistant that finds the optimal move in a Rummikub game from a photo.

Take a picture of your rack and the shared board — the app detects every tile, lets you fix any mistakes, then solves the board and shows you exactly what to play.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [CI/CD](#cicd)
- [Cloud (AWS)](#cloud-aws)
- [Project Structure](#project-structure)
- [Setup and Running](#setup-and-running)
- [API Documentation (Swagger)](#api-documentation-swagger)
- [Testing](#testing)
- [Application Flow](#application-flow)

---

## Overview

Rummikub requires analyzing a complex, constantly changing board and figuring out how to rearrange existing sets to play as many of your own tiles as possible. This is a hard combinatorial problem.

This app solves it by:

1. Taking photos of the board and your rack
2. Detecting and classifying every tile using computer vision (YOLOv8 + ResNet18)
3. Letting you review and correct any detection errors
4. Running an ILP solver to find the move that plays the maximum number of tiles from your rack
5. Walking you through the move step by step with an interactive simulation

---

## Features

- **Tile detection** with a fine-tuned YOLOv8 model, plus IoU-based filtering of duplicate detections
- **Tile classification** into 53 classes (4 colors × 13 values + joker) with ResNet18
- **Automatic rack detection** using HSV color segmentation
- **Review and correction** — edit, add or remove tiles in a list or directly on the original photo
- **Real-time rule validation** — runs, groups, joker handling, and duplicate limits (max 2 copies per tile, max 2 jokers)
- **ILP solver** that maximizes the number of rack tiles played, freely splitting and recombining existing board sets
- **Full joker support** in both validation and solving
- **Step-by-step simulation** of the move, with live rack and board updates
- **JWT authentication** and per-user solution history
- **Model feedback loop** — corrections are stored as labeled training examples for future retraining

---

## Architecture

The system is a three-tier architecture:

- **Mobile app** (React Native + Expo) — captures the rack/board photos, renders the review and simulation screens, and talks to the API gateway over HTTP.
- **Node.js / Express API gateway** — the single entry point for the mobile app. Owns authentication (signup/login, JWT issuance and verification), forwards vision and solver requests to the Python service, and persists users, solved-solution history, and vision feedback in MongoDB. This is also where the OpenAPI/Swagger docs are served.
- **Python / FastAPI service** — stateless compute service that does the actual work: the vision pipeline (rack region detection, YOLOv8 tile detection, ResNet18 classification) and the ILP solver. It has no direct knowledge of users or auth; the Node gateway proxies requests to it.
- **MongoDB** — stores user accounts, saved solutions, and vision-feedback metadata.
- **AWS S3** — stores the photos behind vision-feedback corrections (see [Cloud (AWS)](#cloud-aws)).

The whole stack runs locally with a single `docker compose up`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile app | React Native, Expo, TypeScript |
| API gateway | Node.js, Express, TypeScript, JWT auth |
| Vision & solver service | Python, FastAPI |
| Computer vision | YOLOv8 (Ultralytics), ResNet18 (PyTorch/torchvision), OpenCV |
| Optimization | PuLP (Integer Linear Programming) |
| Database | MongoDB |
| Cloud storage | AWS S3 (boto3) |
| API documentation | Swagger UI / OpenAPI 3.0 (`swagger-jsdoc` on the gateway, native FastAPI docs on the vision service) |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (ghcr.io) |
| Testing | pytest (unit tests + integration tests against a live stack) |

---

## CI/CD

```
pull request ──► CI: unit tests + TypeScript build ──► merge to main ──► CI ──► CD: build & publish Docker images ──► ghcr.io
```

| Workflow | Runs on | What it does |
|---|---|---|
| **CI** ([`ci.yml`](.github/workflows/ci.yml)) | Every pull request to `main`, and every push to `main` | Runs the Python unit tests and compiles the TypeScript API gateway, in parallel |
| **CD** ([`deploy.yml`](.github/workflows/deploy.yml)) | After CI passes on `main` | Builds the `api` and `backend` Docker images and publishes them to GitHub Container Registry |

- `main` is protected: a pull request cannot be merged unless both CI checks pass.
- CD only runs on commits that passed CI, and builds the exact commit CI tested.
- Every image is tagged `latest` and `sha-<commit>`, so any previous version can be pulled again for a rollback.

The published images are public:

```bash
docker pull ghcr.io/bar-nakdimon/rummikub-api:latest
docker pull ghcr.io/bar-nakdimon/rummikub-backend:latest
```

---

## Cloud (AWS)

**S3 — vision feedback storage.** When a user corrects a detected tile, the photo and a JSON file describing the correction are saved as a training example for future model retraining.

- If `S3_BUCKET_NAME` is set, they are uploaded to an S3 bucket ([`s3_storage.py`](backend/vision/s3_storage.py)).
- If it isn't, they are saved to local disk instead, so the project runs without an AWS account.
- Configuration lives in `backend/.env` — copy [`backend/.env.example`](backend/.env.example) and fill in the IAM credentials and bucket name. The file is git-ignored, so credentials are never committed.
- The bucket blocks all public access; only the object key is stored, never a public URL.

`GET http://localhost:8000/storage-status` reports whether S3 or local disk is currently in use.

---

## Project Structure

```
AI-Rummikub-project/
├── backend/                # Python FastAPI service
│   ├── logic/              # Rule validation, ILP solver, move explainer
│   └── vision/             # Detection, classification, rack region, S3 feedback storage
├── api/                    # Node.js/Express gateway: auth, proxying, MongoDB, Swagger
├── mobile/                 # React Native + Expo app
├── tests/
│   ├── unit/               # pytest unit tests (logic, solver, explainer, models)
│   └── test_api_integration.py
├── .github/workflows/      # CI (tests + build) and CD (Docker images → ghcr.io)
└── docker-compose.yml
```

---

## Setup and Running

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Expo Go](https://expo.dev/go) installed on your mobile device
- Your phone and computer on the **same Wi-Fi network**

### Step 1 — Clone the repository

```bash
git clone https://github.com/bar-nakdimon/AI-Rummikub-project.git
cd AI-Rummikub-project
```

### Step 2 — Set your local IP address

Find the IPv4 address of your Wi-Fi adapter (on Windows, run `ipconfig`), e.g. `10.100.102.11`. Then set it in two places:

1. Create `mobile/.env` with:

   ```env
   EXPO_PUBLIC_API_URL=http://YOUR_IP:3000/api
   ```

2. In `docker-compose.yml`, replace:

   ```yaml
   - REACT_NATIVE_PACKAGER_HOSTNAME=YOUR_IP
   ```

### Step 3 — Run

**First run:**
```bash
docker compose up --build
```

**Subsequent runs:**
```bash
docker compose up
```

This starts 4 containers:

| Container | Port | Description |
|---|---|---|
| `rummikub-mongo` | 27017 | MongoDB |
| `rummikub-python-backend` | 8000 | Vision and logic server |
| `rummikub-node-api` | 3000 | REST API gateway |
| `rummikub-mobile` | 8081, 19000-19002 | Expo dev server |

All dependencies install automatically inside Docker — no manual `pip install` or `npm install` needed.

### Step 4 — Connect your phone

1. Wait for the Expo QR code to appear in the terminal
2. Open Expo Go on your phone
3. Scan the QR code

### Stopping

```bash
docker compose down
```

---

## API Documentation (Swagger)

Both backend services expose interactive OpenAPI/Swagger docs once running:

| Service | Swagger UI | Raw OpenAPI JSON |
|---|---|---|
| Node API gateway (auth, vision, solver, solutions) | `http://localhost:3000/api/docs` | `http://localhost:3000/api/docs.json` |
| Python vision/solver service | `http://localhost:8000/docs` | `http://localhost:8000/openapi.json` |

Protected endpoints on the Node API require a JWT: log in via `/api/auth/login` in the docs page, then click **Authorize** and paste the token (`Bearer <token>` is added automatically).

**Node API gateway endpoints** — this is the full surface the mobile app talks to:

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/signup` | — | Create an account |
| POST | `/api/auth/login` | — | Log in, get a JWT |
| GET | `/api/auth/profile` | JWT | Get the logged-in user's profile |
| POST | `/api/vision/analyze` | JWT | Upload rack/board photos, get back detected tiles |
| POST | `/api/vision/feedback` | JWT | Submit a manual tile correction as a training example |
| GET | `/api/vision/health` | JWT | Check that the Python vision service is reachable |
| POST | `/api/solver/solve` | JWT | Get the optimal move for a given `GameState` |
| POST | `/api/solver/validate` | JWT | Validate a `GameState` (runs, groups, joker rules) |
| POST | `/api/solutions` | JWT | Save a solved game state |
| GET | `/api/solutions` | JWT | List the logged-in user's saved solutions |

---

## Testing

### Unit tests

46 pytest unit tests in [`tests/unit/`](tests/unit/) cover the core game logic. They need no server, database or ML models, and run in about a second. **CI runs them automatically on every pull request.**

| File | Covers |
|---|---|
| `test_logic.py` | Groups, runs, jokers filling gaps or extending runs, the 1–13 boundary, duplicate and joker limits |
| `test_solver.py` | Playing from the rack, extending and rearranging board sets, maximizing tiles played, jokers, no-move and invalid-input cases |
| `test_explainer.py` | The step types used by the simulation screen, and the text explanation |
| `test_models.py` | Tile validation (value range, required color) |

Every solver test also checks invariants on the returned solution: each set on the new board is legal, and no tile is lost or duplicated.

```bash
pip install -r backend/requirements-test.txt
python -m pytest tests/unit -v
```

### Integration tests

[`tests/test_api_integration.py`](tests/test_api_integration.py) sends real HTTP requests to the running stack, with no mocking. These tests are **run manually** against `docker compose`, and mirror the project's core user stories:

| Test | User story |
|---|---|
| `test_user_login` | Login |
| `test_upload_game_images` | Upload rack/board photos and get back a detected `GameState` |
| `test_submit_vision_feedback` | Submit a manual correction of a detected tile |
| `test_solve_game_state` | Get the recommended move from the ILP solver |

Two real Rummikub photos (`tests/fixtures/rack.jpg`, `tests/fixtures/table.jpg`) are included so the upload tests exercise genuine detections.

```bash
docker compose up                                  # from the project root, in another terminal
pip install requests pytest
python -m pytest tests/test_api_integration.py -v -s
```

---

## Application Flow

A step-by-step walkthrough of the user journey from login to solution.

### Step 1 — Authentication

Create a new account or log in with an existing one to access the solver.

<img src="https://i.imgur.com/Q4ESpCN.jpeg" width="220"> <img src="https://i.imgur.com/LmqoL0D.jpeg" width="220">

### Step 2 — Upload Photos

Snap a photo of your tile rack and the shared board, then tap **Analyze Photos** to send them for detection.

<img src="https://i.imgur.com/tKqSx4V.jpeg" width="220"> <img src="https://i.imgur.com/KIiJ558.jpeg" width="220">

### Step 3 — Detection Review

Review a summary of all detected tiles and board sets before solving — tap **Edit** to correct errors or **Solve** to proceed.

<img src="https://i.imgur.com/MeDyN6F.jpeg" width="220">

### Step 4 — Review and Edit Tiles

Inspect every detected tile individually; tap any tile to correct it, add tiles the model missed, or reorganize board sets.

<img src="https://i.imgur.com/7JunOJV.jpeg" width="220"> <img src="https://i.imgur.com/UZMBlns.jpeg" width="220">

### Step 5 — Optimal Solution

The ILP solver returns the best possible move — tiles to play, sets to rearrange, and full joker usage explained.

<img src="https://i.imgur.com/eghm6io.jpeg" width="220"> <img src="https://i.imgur.com/mayghI1.jpeg" width="220"> <img src="https://i.imgur.com/V7XIBc4.jpeg" width="220">

### Step 6 — Step-by-Step Simulation

Follow the move one action at a time, with the rack and board updated live at each step.

<img src="https://i.imgur.com/86dqs2d.jpeg" width="220"> <img src="https://i.imgur.com/4X5uWLU.jpeg" width="220"> <img src="https://i.imgur.com/GtgPD3b.jpeg" width="220"> <img src="https://i.imgur.com/Ddtlxq8.jpeg" width="220">

### Step 7 — History

Browse all previously solved games with timestamps and tile counts, and revisit any past solution.

<img src="https://i.imgur.com/ssaR8J1.jpeg" width="220">
