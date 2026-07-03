<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/blueprints/PE_RM_Phase1.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

# Technical Blueprint: Phase 1 - Local Containerization

## I. Objective

**CS / English:** Package the existing Credit Agreement (CA) application into two isolated Docker containers (Backend and Frontend) and orchestrate them locally using Docker Compose. This ensures the application runs completely independently of the local host OS, maintaining consistent dependency resolution and networking.

**Mathematical Formalization:** We are constructing the isolated categorical context $\Gamma_{container}$. We will internalize the application morphisms into two distinct exponential objects ($Y^D_{Backend}$ and $Y^D_{Frontend}$). The Docker Compose file will define the evaluation morphism ($eval$) and the strict networking topology that binds them, ensuring the host context ($X$) remains unpolluted: $\Gamma_{container} \cap \Gamma_{host} = \emptyset$.

## II. Target Architecture & File Tree

Cursor must generate or modify the following files within the existing repository:

Plaintext

```
/ (Project Root)
├── viewer/
│   ├── backend/
│   │   └── Dockerfile          # Exponential Object 1: API & Extraction Engine
│   └── frontend/
│       └── Dockerfile          # Exponential Object 2: React Viewer
├── docker-compose.yml          # The Orchestrator / Context Boundary
└── .env.docker                 # Environment Variable injection (Do not commit to Git)
```

## III. Component Specifications

### Step A: The Backend `Dockerfile` ($Y^D_{Backend}$)

**Purpose:** Containerize the FastAPI server and the `covenant_pipeline` extraction engine.

- **Base Image:** Use `python:3.11-slim` to minimize the attack surface and image weight.
    
- **Domain Dependencies ($D$):** * Copy `requirements.txt` into the container.
    
    - Execute `pip install --no-cache-dir -r requirements.txt`. (This ensures the product of dependencies $T_{Python} \times T_{Pandas} \times T_{FastAPI}$ is strictly bounded).
        
- **Source Code Integration:** Copy the `covenant_pipeline/` package and `viewer/backend/` directories into the container's working directory.
    
- **Network / Ports:** Expose port `8000`.
    
- **Execution Morphism ($eval$):** Define the entrypoint command: `uvicorn viewer.backend.main:app --host 0.0.0.0 --port 8000`.
    

### Step B: The Frontend `Dockerfile` ($Y^D_{Frontend}$)

**Purpose:** Containerize the React/Vite UI.

- **Build Pattern:** Use a **Multi-Stage Build** to separate the compilation environment from the runtime environment.
    
- **Stage 1: The Compiler (Node)**
    
    - Base: `node:20-alpine`.
        
    - Action: Copy `package.json`, run `npm install`, copy `viewer/frontend/src/`, and run `npm run build`. This generates the static HTML/JS/CSS assets.
        
- **Stage 2: The Server (Nginx)**
    
    - Base: `nginx:alpine`.
        
    - Action: Discard the heavy Node environment. Copy _only_ the compiled static assets from Stage 1 into the Nginx serving directory (`/usr/share/nginx/html`).
        
    - Configuration: Inject a custom `nginx.conf` if necessary to handle React Router fallbacks (serving `index.html` for 404s).
        
- **Network / Ports:** Expose port `80`.
    

### Step C: Local Orchestration (`docker-compose.yml`)

**Purpose:** Define the local cluster topology, map volumes, and inject the environment variables.

- **Service 1: `backend`**
    
    - Build context: `./viewer/backend` (or project root, depending on paths).
        
    - Ports: Map host `8000` to container `8000`.
        
    - Environment: Pass `GEMINI_API_KEY` from a local `.env` file into the container.
        
    - **Volume Mounts [CRITICAL]:** * Mount a local `./data` directory to `/app/data` inside the container. This allows you to drop `Credit_Agreement_Hallador.pdf` into a folder on your Mac/PC, and the containerized engine can read it, process it, and write the `final_compiled_payload_audited.json` back to the host filesystem without rebuilding the image.
        
- **Service 2: `frontend`**
    
    - Build context: `./viewer/frontend`.
        
    - Ports: Map host `5173` (or `8080`) to container `80`.
        
    - Dependencies: Use `depends_on: backend` to ensure the API is running before the UI starts.
        
    - Environment / Proxy: Configure Vite/Nginx so that frontend calls to `/api/*` are routed internally to the `backend` service container on port 8000.
