module "network" {
  source = "./modules/network"

  aws_region = var.aws_region
}

module "iam" {
  source = "./modules/iam"

  aws_region        = var.aws_region
  data_bucket_arn   = var.data_bucket_arn
  gemini_secret_arn = var.gemini_secret_arn
}

module "storage" {
  source = "./modules/storage"

  data_bucket_arn            = var.data_bucket_arn
  s3files_sync_role_arn      = module.iam.s3files_sync_role_arn
  vpc_id                     = module.network.vpc_id
  public_subnet_ids          = module.network.public_subnet_ids
  backend_security_group_id  = module.network.backend_sg_id
  pipeline_security_group_id = module.network.pipeline_sg_id
}

module "ecs" {
  source = "./modules/ecs"

  aws_region    = var.aws_region
  desired_count = var.desired_count

  backend_repository_url  = var.backend_repository_url
  frontend_repository_url = var.frontend_repository_url
  backend_image_digest    = var.backend_image_digest
  frontend_image_digest   = var.frontend_image_digest
  gemini_secret_arn       = var.gemini_secret_arn

  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  alb_sg_id         = module.network.alb_sg_id
  frontend_sg_id    = module.network.frontend_sg_id
  backend_sg_id     = module.network.backend_sg_id
  pipeline_sg_id    = module.network.pipeline_sg_id
  frontend_tg_arn   = module.network.frontend_tg_arn
  alb_dns_name      = module.network.alb_dns_name

  service_connect_namespace_arn  = module.network.service_connect_namespace_arn
  service_connect_namespace_name = module.network.service_connect_namespace_name

  task_execution_role_arn = module.iam.task_execution_role_arn
  backend_task_role_arn   = module.iam.backend_task_role_arn
  pipeline_task_role_arn  = module.iam.pipeline_task_role_arn

  s3files_file_system_arn  = module.storage.file_system_arn
  s3files_access_point_arn = module.storage.access_point_arn
}
