# Taptupo Chatbot

This repository contains the infrastructure, backend Lambdas, and static frontend for the Taptupo generative AI chatbot.

## Structure

- **infra/** — Terraform for AWS (Cognito, S3, CloudFront, RDS, EC2, API Gateway, Lambdas)
- **lambda/admin/** — Python FastAPI + Mangum for admin CRUD
- **lambda/chat/**  — Python FastAPI + Mangum for chat + RAG + MCP
- **static/**       — index.html + vanilla JS client

