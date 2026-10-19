# Rummikub Solver

An AI-powered mobile assistant that finds the optimal move in a Rummikub game from a photo.

Take a picture of your rack and the shared board — the app detects every tile, lets you fix any mistakes, then solves the board and shows you exactly what to play.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup and Running](#setup-and-running)
- [API Endpoints](#api-endpoints)
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

**Vision and Detection**
- Photo-based tile detection using a fine-tuned YOLOv8 model
- Tile classification into 53 classes (4 colors x 13 values + joker) using ResNet18
- Automatic rack region detection using HSV color segmentation
- Duplicate detection filtering via IoU

**Review and Editing**
- Read-only review screen showing the detected rack and board
- Full tile editor — change color, number, or type (regular/joker)
- Add tiles the model missed
- Remove false positive detections
- Merge two board sets or move a tile between sets
- Vision overlay editor — tap bounding boxes directly on the original photo to edit
- Undo the last edit

**Game Logic and Validation**
- Real-time board validation (runs, groups, joker handling)
- Duplicate tile detection (max 2 copies of any tile, max 2 jokers)
- Full joker support in validation and solving

**Solver**
- ILP solver maximizing the number of rack tiles played
- Board rearrangement — existing sets can be split and recombined freely
- Step-by-step interactive simulation with live rack and board updates

**App**
- User authentication (JWT-based)
- Solution history — view any previously solved game
- Cross-platform mobile app (iOS and Android via Expo Go)
- Model feedback loop — corrections you make while editing are stored as labeled training examples for future retraining

---

## Architecture

The system is a three-tier architecture:

- **Mobile app** (React Native + Expo) — captures the rack/board photos, renders the review and simulation screens, and talks to the API gateway over HTTP.
- **Node.js / Express API gateway** — the single entry point for the mobile app. Owns authentication (signup/login, JWT issuance and verification), forwards vision and solver requests to the Python service, and persists users, solved-solution history, and vision feedback in MongoDB.
- **Python / FastAPI service** — stateless compute service that does the actual work: the vision pipeline (rack region detection, YOLOv8 tile detection, ResNet18 classification) and the ILP solver. It has no direct knowledge of users or auth; the Node gateway proxies requests to it.
- **MongoDB** — stores user accounts, saved solutions, and vision-feedback metadata.

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
| Containerization | Docker, Docker Compose |
| Testing | pytest + `requests` (integration tests against a live stack) |

---

## Project Structure

```
rummikub-project/
├── backend/                    # Python FastAPI — vision + logic
│   ├── main.py                 # FastAPI app, routes, /storage-status
│   ├── logic/                  # ILP solver, validation, move explainer
│   │   ├── solver_ilp.py
│   │   ├── logic.py
│   │   └── explainer.py
│   └── vision/                 # Detection, classification, rack region, feedback
│       ├── vision_pipeline.py
│       ├── detector_service.py
│       ├── classifier_service.py
│       ├── rack_region.py
│       └── feedback_service.py
│
├── api/                         # Node.js Express API gateway
│   └── src/
│       ├── config/              # DB connection, JWT config
│       ├── controllers/         # Auth, vision, solver, solution-history
│       ├── routes/               # Express routers
│       ├── services/             # Vision proxying, feedback, image normalization
│       ├── models/               # Data models (User, Solution, VisionFeedback)
│       └── middleware/           # JWT auth middleware
│
├── mobile/                       # React Native + Expo
│   ├── app/
│   │   ├── (auth)/               # Login, signup
│   │   └── (main)/
│   │       ├── (tabs)/           # Home tab
│   │       ├── review-edit.tsx   # Tile/board editor
│   │       ├── solution.tsx      # Solver result screen
│   │       ├── simulation.tsx    # Step-by-step move simulation
│   │       └── history.tsx       # Solution history
│   ├── components/
│   ├── context/
│   ├── services/                 # api.ts — typed API client (axios)
│   └── types/
│
├── tests/                        # Integration tests (pytest, run against docker compose)
│   ├── test_api_integration.py
│   └── fixtures/                 # Sample rack/table photos used by the tests
│
└── docker-compose.yml
```

---

## Setup and Running

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Expo Go](https://expo.dev/go) installed on your mobile device
- Your phone and computer on the **same Wi-Fi network**

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/bar-nakdimon/AI-Rummikub-project.git
cd AI-Rummikub-project
```

---

### Step 2 — Find your local IP address

**Windows:**
```powershell
ipconfig
```

Look for the IPv4 address on your Wi-Fi adapter, e.g. `10.100.102.11`.

---

### Step 3 — Set your local IP in two places

Create the mobile environment file:

```bash
touch mobile/.env
```

Open `mobile/.env` in your editor and paste:

```env
EXPO_PUBLIC_API_URL=http://YOUR_IP:3000/api
```

Then open `docker-compose.yml` and replace:

```yaml
- REACT_NATIVE_PACKAGER_HOSTNAME=YOUR_IP
```

---

### Step 4 — Run

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

---

### Step 5 — Connect your phone

1. Wait for the Expo QR code to appear in the terminal
2. Open Expo Go on your phone
3. Scan the QR code

---

### Stopping

```bash
docker compose down
```

---

## API Endpoints

These are the Node API gateway endpoints — the full surface the mobile app talks to:

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

Integration tests live in `tests/test_api_integration.py` and run as real HTTP requests against the live stack — no mocking. They mirror the project's core user stories one-to-one:

| Test | User story |
|---|---|
| `test_user_login` | Login |
| `test_upload_game_images` | Upload rack/board photos and get back a detected `GameState` |
| `test_submit_vision_feedback` | Submit a manual correction of a detected tile |
| `test_solve_game_state` | Get the recommended move from the ILP solver |

Two real Rummikub photos (`tests/fixtures/rack.jpg`, `tests/fixtures/table.jpg`) are included so the upload tests exercise genuine detections out of the box.

**To run:**

```bash
docker compose up                                  # from the project root, in another terminal
pip install requests pytest --break-system-packages
pytest tests/test_api_integration.py -v -s
```

---

## Application Flow

A step-by-step walkthrough of the user journey from login to solution.

---

### Step 1 — Authentication

Create a new account or log in with an existing one to access the solver.

<img src="https://i.imgur.com/Q4ESpCN.jpeg" width="220"> <img src="https://i.imgur.com/LmqoL0D.jpeg" width="220">

---

### Step 2 — Upload Photos

Snap a photo of your tile rack and the shared board, then tap **Analyze Photos** to send them for detection.

<img src="https://i.imgur.com/tKqSx4V.jpeg" width="220"> <img src="https://i.imgur.com/KIiJ558.jpeg" width="220">

---

### Step 3 — Detection Review

Review a summary of all detected tiles and board sets before solving — tap **Edit** to correct errors or **Solve** to proceed.

<img src="https://i.imgur.com/MeDyN6F.jpeg" width="220">

---

### Step 4 — Review and Edit Tiles

Inspect every detected tile individually; tap any tile to correct it, add tiles the model missed, or reorganize board sets.

<img src="https://i.imgur.com/7JunOJV.jpeg" width="220"> <img src="https://i.imgur.com/UZMBlns.jpeg" width="220">

---

### Step 5 — Optimal Solution

The ILP solver returns the best possible move — tiles to play, sets to rearrange, and full joker usage explained.

<img src="https://i.imgur.com/eghm6io.jpeg" width="220"> <img src="https://i.imgur.com/mayghI1.jpeg" width="220"> <img src="https://i.imgur.com/V7XIBc4.jpeg" width="220">

---

### Step 6 — Step-by-Step Simulation

Follow the move one action at a time, with the rack and board updated live at each step.

<img src="https://i.imgur.com/86dqs2d.jpeg" width="220"> <img src="https://i.imgur.com/4X5uWLU.jpeg" width="220"> <img src="https://i.imgur.com/GtgPD3b.jpeg" width="220"> <img src="https://i.imgur.com/Ddtlxq8.jpeg" width="220">

---

### Step 7 — History

Browse all previously solved games with timestamps and tile counts, and revisit any past solution.

<img src="https://i.imgur.com/ssaR8J1.jpeg" width="220">
