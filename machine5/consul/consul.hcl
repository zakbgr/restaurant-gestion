# Configuration Consul Client pour Machine 5
datacenter = "restaurant-dc"
data_dir = "/opt/consul/data"
log_level = "INFO"

# Mode client (se connecte au leader sur Machine 1)
server = false

# Adresse du serveur Consul (Machine 1)
retry_join = ["192.168.1.1:8500"]  # Remplacez par l'IP de Machine 1

# Interface réseau
bind_addr = "0.0.0.0"
client_addr = "0.0.0.0"

# Port Consul
ports {
  http = 8500
  dns = 8600
}

# Activation de l'UI Consul
ui_config {
  enabled = false
}