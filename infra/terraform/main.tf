terraform {
  required_version = "= 1.17.2"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "= 4.7.0"
    }
  }
}

provider "docker" {
  host = var.docker_host
}

resource "docker_network" "private" {
  name     = "${var.stack_name}-private"
  internal = true
  driver   = "bridge"
  lifecycle {
    prevent_destroy = true
  }
}

resource "docker_volume" "app_data" {
  name = "${var.stack_name}-app-data"
  lifecycle {
    prevent_destroy = true
  }
}

resource "docker_volume" "temporal_data" {
  name = "${var.stack_name}-temporal-data"
  lifecycle {
    prevent_destroy = true
  }
}
