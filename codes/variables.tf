#Create variable names

variable "project_name" {
  description = "GCP project ID"
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
}

variable "gcs_bucket_name" {
  description = "GCS bucket name"
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "bq_dataset_name" {
  description = "BQ dataset name"
}

variable "spark_cluster_name" {
  description = "DataProc cluster name"
}