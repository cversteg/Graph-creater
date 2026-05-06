variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "environment" {
  description = "Deployment environment (prod/dev)"
  type        = string
  default     = "prod"
}

variable "project" {
  description = "Project short name used in resource naming"
  type        = string
  default     = "scatter-app"
}
