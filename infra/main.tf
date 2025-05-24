provider "aws" {
  region = "eu-west-1"
}

# Cognito
resource "aws_cognito_user_pool" "users" {
  name = "taptupo-users"
}
resource "aws_cognito_user_pool_client" "web" {
  name              = "taptupo-web-client"
  user_pool_id      = aws_cognito_user_pool.users.id
  generate_secret   = false
  allowed_oauth_flows       = ["code"]
  allowed_oauth_scopes      = ["openid","email","profile"]
  callback_urls            = ["https://taptupo.com/"]
  logout_urls             = ["https://taptupo.com/"]
  supported_identity_providers = ["COGNITO","Google"]
}

# S3 + CloudFront
resource "aws_s3_bucket" "site" {
  bucket = "taptupo-static"
  acl    = "public-read"
  website { index_document = "index.html" }
}
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = aws_s3_bucket.site.website_endpoint
    origin_id   = "S3-taptupo"
  }
  enabled             = true
  default_root_object = "index.html"
}

# RDS Postgres
resource "aws_db_instance" "postgres" {
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t4g.micro"
  allocated_storage = 20
  name              = "taptupoadmin"
  username          = var.db_user
  password          = var.db_pass
  skip_final_snapshot = true
}

# EC2 for Qdrant
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter { name = "name"; values = ["ubuntu/images/hvm-ssd/ubuntu-22.04-amd64-server-*"] }
}
resource "aws_instance" "qdrant" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small"
  user_data = <<-EOF
    #!/bin/bash
    docker run -d -p 6333:6333 qdrant/qdrant
  EOF
}

# Lambdas + API Gateway
module "lambda_admin" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = "taptupo-admin"
  handler       = "handler.app"
  runtime       = "python3.11"
  source_path   = "../lambda/admin"
  environment = {
    DB_HOST     = aws_db_instance.postgres.address
    DB_USER     = var.db_user
    DB_PASSWORD = var.db_pass
  }
}
module "lambda_chat" {
  source        = "terraform-aws-modules/lambda/aws"
  function_name = "taptupo-chat"
  handler       = "handler.app"
  runtime       = "python3.11"
  source_path   = "../lambda/chat"
  environment = {
    QDRANT_URL        = aws_instance.qdrant.public_dns
    QDRANT_PORT       = "6333"
    OPENAI_API_KEY    = var.openai_key
    ANTHROPIC_API_KEY = var.anthropic_key
  }
}
resource "aws_api_gateway_rest_api" "api" {
  name = "taptupo-api"
}
