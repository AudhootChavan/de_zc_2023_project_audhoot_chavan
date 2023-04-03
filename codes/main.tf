terraform {
  required_version = ">= 1.0"
  backend "local" {}  # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source  = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project_name
  region = var.region
}

# Data lake bucket - Staging bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = var.gcs_bucket_name 
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }
  force_destroy = true

}


# DWH - Dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.bq_dataset_name
  project    = var.project_name
  location   = var.region
  delete_contents_on_destroy = true
}


# Dataproc cluster

resource "google_dataproc_cluster" "dataproc-cluster" {
  name     = var.spark_cluster_name
  project    = var.project_name
  region   = var.region

  cluster_config {
    staging_bucket = var.gcs_bucket_name

    master_config {
      num_instances = 1
      machine_type  = "n2-standard-2"
      disk_config {
        boot_disk_type    = "pd-ssd"
        boot_disk_size_gb = 50
      }
    }

    # Override or set some custom properties
    software_config {
      image_version = "2.0-debian10"
      override_properties = {
        "dataproc:dataproc.allow.zero.workers" = "true"
      }
    }



  }
}