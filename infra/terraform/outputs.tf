output "private_network" {
  value = docker_network.private.name
}

output "app_volume" {
  value = docker_volume.app_data.name
}

output "temporal_volume" {
  value = docker_volume.temporal_data.name
}
