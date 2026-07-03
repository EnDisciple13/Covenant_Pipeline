<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/PE_Roadmap_M1.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_project_docs.py -->

---
id: projects-covenant-platform-engineering-PE_Roadmap_M1
type: project_strategy
status: draft
dependencies:
tags: []
invariants: []
---
## Platform Engineering Roadmap: The CA Pipeline

**Milestone 1 (M1)** deploys the Covenant Extraction Pipeline to cloud infrastructure. **Milestone 2 (M2)** generalizes to an Internal Developer Platform (IDP) — see [PE_Roadmap_M2.md](PE_Roadmap_M2.md).

Planning docs for the infrastructure layer. Phase 1 implementation: see [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) in the `covenant_pipeline` repo.

**Technical blueprints (detailed design specs):**

| Phase | Blueprint | Status |
|-------|-----------|--------|
| Phase 1: Local Containerization | [PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | Implemented — see [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md) |
| Phase 2: Target Cloud Topology (AWS) | [PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md) | Design only |
| Phase 3: Infrastructure as Code (Terraform) | [PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md) | Design only |
| Phase 4: CI/CD Orchestration | [PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md) | Design only |

### I. The Setup & Goal

**The Setup:** The Application Layer is complete. You have a deterministic Credit Agreement Python engine, a FastAPI backend, and a React frontend. Currently, this exists as raw code (morphisms) executing in the highly volatile, un-closed ambient environment of your local operating system.

**The Goal:** Transition into the Platform Engineer role by constructing the infrastructure layer. You will package the application into an immutable mathematical object (Docker), define a target enterprise cloud topology (AWS/Azure), and write the declarative functor (Terraform) that idempotently maps your code to that live environment.

### Phase 1: Local Containerization (Constructing the Exponential Object)

**Blueprint:** [PE_RM_Phase1.md](blueprints/PE_RM_Phase1.md) | **Implementation:** [Docker_Documentation.md](https://github.com/endisciple13/covenant_pipeline/blob/main/Docker_Documentation.md)

Before the pipeline can touch a cloud network, it must be mathematically isolated. This phase ensures the software runs exactly the same way in Garland, Texas, as it will on a server in an East Coast data center.

- **Step A: The Backend `Dockerfile`**
    
    - Define the base image (e.g., `python:3.11-slim`).
        
    - Define the product of dependencies ($D$) via `requirements.txt`.
        
    - Expose the API port (8000).
        
- **Step B: The Frontend `Dockerfile`**
    
    - Define a Node environment to build the React/Vite viewer.
        
    - Serve the static assets using a lightweight web server (Nginx).
        
- **Step C: Orchestration (`docker-compose.yml`)**
    
    - Link the two containers locally so the React frontend can talk to the FastAPI backend over a virtual local network.
        

### Phase 2: Target Category Architecture (Defining the Cloud Topology)

**Blueprint:** [PE_RM_Phase2.md](blueprints/PE_RM_Phase2.md)

You need to identify the exact objects in the target Cloud Category ($\mathcal{D}_{Cloud}$) that will host your containers. Given an enterprise banking context, you will design this using scalable, serverless container hosting.

- **Step A: The Container Registry**
    
    - _AWS:_ Elastic Container Registry (ECR) / _Azure:_ Azure Container Registry (ACR).
        
    - This is the storage repository for your built $Y^D$ objects.
        
- **Step B: The Compute Engine**
    
    - _AWS:_ ECS Fargate / _Azure:_ Azure Container Apps.
        
    - This is the execution environment that runs the $eval$ morphism. It provisions CPU and RAM dynamically without you managing the underlying virtual machines.
        
- **Step C: Networking & IAM**
    
    - Define the Virtual Private Cloud (VPC), Subnets, and Load Balancer to route HTTP traffic to your container securely.
        

### Phase 3: Infrastructure as Code (Writing the Functor)

**Blueprint:** [PE_RM_Phase3.md](blueprints/PE_RM_Phase3.md)

Manual clicking in a cloud portal is strictly prohibited in Platform Engineering. You will write the structural delta tracking morphism ($\Delta_C$) using **Terraform**.

- **Step A: Provider Configuration**
    
    - Initialize the Terraform state to track your target cloud (AWS or Azure).
        
- **Step B: Resource Definitions**
    
    - Write declarative blocks for the Registry, the Compute Cluster, the Task Definitions (pointing to your Docker images), and the Network interfaces.
        
- **Step C: The State Functor Execution**
    
    - Run `terraform plan` to compute the exact diff between the abstract code and the live cloud.
        
    - Run `terraform apply` to execute the idempotent mutations.
        

### Phase 4: CI/CD Orchestration (The Control Loop)

**Blueprint:** [PE_RM_Phase4.md](blueprints/PE_RM_Phase4.md)

The final step is automating the entire pipeline so that an update to the SWE code automatically updates the live architecture.

- **Step A: GitHub Actions Workflow**
    
    - Write a YAML file that triggers when you push code.
        
    - **Job 1:** Run Phase 3a `audit.py` (fail the build if integrity is compromised).
        
    - **Job 2:** Build the new Docker Images.
        
    - **Job 3:** Push the images to the Cloud Registry.
        
    - **Job 4:** Trigger the Terraform state update to pull the new images into the live Compute Engine.
