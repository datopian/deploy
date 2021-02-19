variable "region" {
  default = "europe-west1"
}

variable "zone" {
  default = "europe-west1-b"
}

variable "kubernetes_version" {
  default = "1.16.15-gke.6000"
}

variable "cluster_name" {
  #default = "datahub-staging"
  default = "datahub-production" # Production
}

variable "node_pool_name" {
  #default = "staging-node-pool"
  default = "production-node-pool" # Production
}

variable "load_balancer_ip" {
  #default = "34.77.5.20"
  default = "35.195.246.183" # Production
}

variable "load_balancer_name" {
  #default = "datahub-nginx"
  default = "datahub-nginx-production" # Production
}

module "gke" {
  source                   = "terraform-google-modules/kubernetes-engine/google"
  version                  = "9.2.0"
  project_id               = "datahub-305010"
  name                     = var.cluster_name
  network                  = "default"
  subnetwork               = "default"
  ip_range_pods            = ""
  ip_range_services        = ""
  regional                 = true
  region                   = var.region
  zones                    = [var.zone]
  create_service_account   = true
  kubernetes_version       = var.kubernetes_version
  remove_default_node_pool = true
  http_load_balancing      = true

  node_pools = [
    {
      name                = var.node_pool_name
      machine_type        = "n1-standard-4"
      min_count           = 2
      max_count           = 2
      local_ssd_count     = 0
      disk_size_gb        = 100
      disk_type           = "pd-standard"
      image_type          = "COS"
      auto_repair         = true
      auto_upgrade        = true
      preemptible         = false
    }
  ]
}

## IP addreses are already reserved so skiping for now
resource "google_compute_address" "ip_address" {
  project       = "datahub-305010"
  name          = var.load_balancer_name
  region        = var.region
}
