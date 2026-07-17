locals {
  backend_digest  = lower(replace(var.backend_image_digest, "sha256:", ""))
  frontend_digest = lower(replace(var.frontend_image_digest, "sha256:", ""))

  backend_image  = "${var.backend_repository_url}@sha256:${local.backend_digest}"
  frontend_image = "${var.frontend_repository_url}@sha256:${local.frontend_digest}"

  covenant_env = [
    { name = "COVENANT_PDF_PATH", value = "/app/data/Credit_Agreement_Hallador.pdf" },
    { name = "COVENANT_OUTPUT_DIR", value = "/app/data/out" },
    { name = "COVENANT_AUDITED_JSON", value = "/app/data/out/final_compiled_payload_audited.json" },
    { name = "COVENANT_DISPATCH_QUEUE_JSON", value = "/app/data/out/dispatch_queue_output.json" },
  ]

  gemini_secret = [
    {
      name      = "GEMINI_API_KEY"
      valueFrom = var.gemini_secret_arn
    },
  ]
}

resource "aws_ecs_cluster" "this" {
  name = var.project_name

  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}/backend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project_name}/frontend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/ecs/${var.project_name}/pipeline"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.backend_task_role_arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = local.backend_image
      essential = true
      command = [
        "uvicorn",
        "main:app",
        "--app-dir",
        "viewer/backend",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
      ]
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
          name          = "backend"
        },
      ]
      environment = local.covenant_env
      secrets     = local.gemini_secret
      mountPoints = [
        {
          sourceVolume  = "app-data"
          containerPath = "/app/data"
          readOnly      = true
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])

  volume {
    name = "app-data"

    s3files_volume_configuration {
      file_system_arn  = var.s3files_file_system_arn
      access_point_arn = var.s3files_access_point_arn
    }
  }
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.task_execution_role_arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = local.frontend_image
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])
}

resource "aws_ecs_task_definition" "pipeline" {
  family                   = "${var.project_name}-pipeline"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.pipeline_task_role_arn

  container_definitions = jsonencode([
    {
      name       = "pipeline"
      image      = local.backend_image
      essential  = true
      entryPoint = ["covenant-pipeline"]
      command = [
        "run",
        "--pdf",
        "/app/data/Credit_Agreement_Hallador.pdf",
        "--output-dir",
        "/app/data/out",
      ]
      environment = local.covenant_env
      secrets     = local.gemini_secret
      mountPoints = [
        {
          sourceVolume  = "app-data"
          containerPath = "/app/data"
          readOnly      = false
        },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.pipeline.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    },
  ])

  volume {
    name = "app-data"

    s3files_volume_configuration {
      file_system_arn  = var.s3files_file_system_arn
      access_point_arn = var.s3files_access_point_arn
    }
  }
}

resource "aws_ecs_service" "backend" {
  name            = "backend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.backend_sg_id]
    assign_public_ip = true
  }

  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_arn

    service {
      port_name = "backend"

      client_alias {
        port     = 8000
        dns_name = "backend"
      }
    }
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}

resource "aws_ecs_service" "frontend" {
  name            = "frontend"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.public_subnet_ids
    security_groups  = [var.frontend_sg_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.frontend_tg_arn
    container_name   = "frontend"
    container_port   = 80
  }

  service_connect_configuration {
    enabled   = true
    namespace = var.service_connect_namespace_arn
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
}
