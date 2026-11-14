variable "stack_name" {
  type        = string
  default     = "governed-dataops"
  description = "Names only the private network and persistent volumes. Match DATAOPS_STACK in Compose."
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,47}$", var.stack_name))
    error_message = "Use a lowercase name of at most 48 characters."
  }
}

variable "docker_host" {
  type        = string
  default     = "unix:///var/run/docker.sock"
  description = "Local Docker daemon. Remote daemons are outside the reference deployment."
  validation {
    condition     = startswith(var.docker_host, "unix:///")
    error_message = "The reference profile supports a local Unix socket only."
  }
}
