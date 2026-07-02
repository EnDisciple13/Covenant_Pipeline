<!-- MIRROR: auto-synced from notes/projects/covenant/platform-engineering/PE_Roadmap_M2.md - do not edit directly. Edit the canonical file in the notes repo and run scripts/sync_pe_docs.py -->

# Enterprise Platform Architecture: The Transition to Milestone 2

**Prerequisite:** M1 Phases 1–4 complete — see [PE_Roadmap_1.md](PE_Roadmap_1.md).

## Part I: The Operational Distinction (M1 vs. M2)

To architect a system top-down, you must cleanly separate the act of deploying an application from the act of building a deployment engine.

### Milestone 1 (M1): Cloud Engineering (The Localized Proof)

**The Objective:** Containerize a specific application (the Covenant Extraction Pipeline) and manually map it to a live cloud topology (AWS/Azure).

- **The Execution:** You wrote a `Dockerfile` specifically for the CA backend. You wrote Terraform code specifically to provision an ECS Fargate cluster for the CA pipeline. You built a GitHub Actions workflow specifically to deploy this one repository.
    
- **Why M1 was Mathematically Necessary:** You cannot abstract a system you have not physically built. Before you can write a generalized functor to map _any_ developer's code to the cloud, you must manually define the source and target categories. M1 was the physical grunt work of learning exactly which IAM roles, VPC subnets, and container ports are required to make the cloud function. You built a single, highly engineered car.
    

### Milestone 2 (M2): Platform Engineering (The Universal Functor)

**The Objective:** Abstract the localized logic of M1 into an **Internal Developer Platform (IDP)**.

- **The Execution:** You are no longer managing the flow of the document data; you are managing the flow of the software itself. You build a standardized, automated runway so that _any_ data scientist or developer can deploy their logic without needing to understand the underlying infrastructure. You are building the factory that mass-produces the cars.
    

## Part II: The Phase 3 Refactor (Infrastructure as Code Abstraction)

In M1, your Terraform was hardcoded. In M2, your Terraform becomes a **Module**. This is the core engine of the IDP.

### 1. The Shift to Agnostic Modules

You extract all the specific names (like `ca_pipeline_cluster`) and replace them with generic variables. You build a module called `standard_enterprise_api`.

**The Module Inputs (Variables):** Instead of the developer writing 500 lines of Terraform to provision networking and compute, your platform only requires them to pass a few operational parameters to your module:

- `app_name` (e.g., "real-estate-extractor")
    
- `environment` (e.g., "dev", "prod")
    
- `cpu_allocation` (e.g., "1024")
    
- `memory_allocation` (e.g., "2048")
    
- `port_number` (e.g., "8000")
    

### 2. The Abstraction Layer

When the module receives these variables, the platform automatically generates the complex AWS resources in the background:

- Dynamically injects the `app_name` into the AWS Load Balancer rules.
    
- Automatically assigns the container to the bank’s secure private subnets.
    
- Provisions the exact CPU/RAM requested without the developer ever logging into the AWS Console.
    

## Part III: The Phase 4 Refactor (Policy-as-Code & Security Axioms)

A platform is useless if it allows developers to deploy vulnerable code. M2 requires injecting strict, automated mathematical constraints into the CI/CD pipeline (GitHub Actions) _before_ the code is allowed to reach the cloud environment.

### 1. Infrastructure Axioms (`tfsec` / `checkov`)

Before the Terraform is executed (`terraform apply`), the pipeline runs a static analysis tool against the infrastructure code.

- **The Constraint:** It checks for violations of the bank's architecture rules. For example, if a developer accidentally modified the module to open Port 22 (SSH) to the public internet, `tfsec` instantly fails the build.
    
- **The Value:** The platform enforces the network boundary deterministically. The developer cannot bypass it.
    

### 2. Software Axioms (`trivy`)

Before the Docker container is pushed to the enterprise registry (ECR/ACR), the pipeline scans the physical container image.

- **The Constraint:** `trivy` scans the Python dependencies and the base OS layer for known vulnerabilities (CVEs). If a developer uses an outdated version of Pandas with a known memory leak, the build fails.
    
- **The Value:** You guarantee that every object entering the cloud topology is structurally sound.
    

## Part IV: Phase 5 (The Golden Path Template)

This is the final abstraction. The end-user (the developer) should not even need to look at your Terraform modules or your CI/CD YAML files.

### 1. The Template Repository

You create a master repository in GitHub called `enterprise-api-template`. This repository contains:

- A highly optimized, generic `Dockerfile`.
    
- A `main.tf` file that already calls your `standard_enterprise_api` module.
    
- A `.github/workflows/deploy.yml` file that already contains the `tfsec` and `trivy` security gates.
    

### 2. The Developer Experience (Self-Service)

When a new analyst wants to build an app, they do not start from scratch. They click "Use this Template." They drop their local Python script (their extraction logic) into the `src/` folder and push to the `main` branch. The platform takes over entirely. The security scans run, the infrastructure provisions, and the container deploys. The cognitive load of cloud infrastructure is completely removed from the developer.

## Part V: **[Analogy]** The Curry-Howard-Lambek Formalism

To internalize this architecture top-down, view the transition from M1 to M2 through the rigor of the Curry-Howard-Lambek correspondence. While cloud engineering is not pure type theory, mapping the structural logic provides a clear operational blueprint.

- **Propositions as Types (The Axioms):** The bank's security requirements (no public IPs, secure memory allocation, scanned dependencies) are the formal _Types_. In M2, your Policy-as-Code (`tfsec`/`trivy`) acts as the strict Type-Checker.
    
- **Proofs as Programs (The Developer Code):** The specific Python extraction script written by the data scientist is the _Proof_. It is the localized logic meant to solve a specific problem.
    
- **Platform as the Functor (The Automated Mapping):** You are building a functor that maps objects from the category of "Local Developer Environments" to the category of "Production Cloud Environments."
    
- **The Structural Integrity:** A functor must preserve the structure of the category. Your platform (the IDP) ensures that no proof (program) can be evaluated (deployed) unless it cleanly passes the type-checker (Policy-as-Code).
    

You are no longer just writing proofs. You are building the formal logical framework in which all future proofs at the bank must be constructed.
