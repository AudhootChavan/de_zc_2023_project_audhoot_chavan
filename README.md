# Build an end-to-end automated data pipeline to visualise stock values of top 5 technology companies and how they are correlated with news article sentiments.

This project is created by me for the [Data Engineering Zoomcamp 2023](https://github.com/DataTalksClub/data-engineering-zoomcamp).  

## Contents
- [Problem statement and project description](#problem-statement-and-project-description)
- [Technologies, tools and data sources used](#technologies-tools-and-data-sources-used)
- [Pipeline diagram](#pipeline-diagram)
- [Pipeline explanation](#pipeline-explanation)
- [How to replicate](#how-to-replicate)
- [Dashboard and results](#dashboard-and-results)
- [Scope for improvement](#scope-for-improvement)
- [Reviewing criteria](#reviewing-criteria)

## Problem statement and project description
We often read online when someone tweets something controversial or if there is a breakthrough in science and tech or if a tragedy strikes, the stock prices of companies move up or down rapidly in response to those. It would definitely be in interest of individuals investing in stocks or companies monitoring their market value to keep track of the internet for news articles/social media/social networks and their subsequent impact on stock values.  
  
This task however is complex and would require tremendous efforts to identify important signals and setup infrastructure to track those. My project aims to implement a small subset of this task by creating an end-to-end automated pipeline to pull stock related data from Alpha Vantage API and push it into a dashboard to visualise stock values and their correlation with news article sentiments. We will do this by taking daily adjusted closing stock value in USD and daily average sentiment of news articles where a respective stock/company/ticker is mentioned. Both data points are available via the [Alpha Vantage API](https://www.alphavantage.co/documentation/). We will consider only technology stocks and identify top 5 by market cap. Reference [here](https://www.nasdaq.com/market-activity/stocks/screener).  
  
This project can mainly be used for academic purposes and with a little bit of tweaking may also be used for investment related decision making with near real time monitoring. The latter part however is not covered in this project and should be considered as scope for improvement. 

## Technologies, tools and data sources used
- Alpha Vantage API - For stock values & stock sentiments.  
  
- Docker - For containerization of the pipeline.
- Python - To build the data pipeline.
- Terraform - Infrastructure-as-a-Service (IaaS) tool to manage GCP resources.
- Prefect - Orchestration tool to build deployments and monitor tasks and flows.
- Spark - To make data transformations on raw data.
- Google Cloud Platform (GCP) 
  - Google Cloud Storage (GCS) - Data Lake. 
  - Big Query (BQ DWH) - Data warehouse.
  - DataProc Cluster - Spark cluster to run spark jobs. 
- Looker Studio - To create dashboard and visualise the results.



## Pipeline diagram
 
<img width="602" alt="Pipeline Diagram" src="https://user-images.githubusercontent.com/12958946/229422092-4eb7c53d-8d6e-4aac-9e8a-0292fc23dced.PNG">


## Pipeline explanation
- The pipeline is written in python and is run entirely inside a docker container. The docker image is created using a python base image with version 3.9. Refer to the *Dockerfile* for more details and *requirements.txt* for the python libraries used/installed.  
  
- Prefect library/prefect cloud is used for orchestration to create flows/tasks and pipeline deployments to monitor runs. The prefect server is running in the cloud and the prefect agent is running in the docker container. 

- Terraform is used to manage GCP resources - GCS, BQ DWH and DataProc Cluster. Relevant variables are defined in the *variables.tf* file for reproducibility. Resource configuration is set in *main.tf* file. Since our data size is small, for the DataProc cluster we are using 1 master and no workers along with lowest compute configuration.  

- *pipeline_deployment_build.py* is the main pipeline file written in python and is built to be deployed on the prefect cloud. The main pipeline file has 4 important functions -> **pull_time_series_stock_data**, **pull_time_series_stock_sentiment_data**, **upload_to_gcs** and **submit_spark_job**.  

  - **The pull_time_series_stock_data** function makes API calls to Alpha Vantage and pulls time series daily adjusted data for the stocks we have defined in our symbols dictionary. For each stock we need to make one call to pull this data. Example call - https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol=IBM&apikey=demo&outputsize=full. We are storing only 4 fields when creating the data frame -> Stock_Name(Name of the ticker), Stock(Ticker), Day(Date in day format) & Value(The daily adjusted closing value in USD).  

  - **The pull_time_series_stock_sentiment_data** function makes calls to Alpha Vantage to pull sentiment data taking 5 days at a time for each stock. This is because the response will return a maximum of 200 articles and their sentiments at a time so if we are pulling yearlong data, we will need to do this in batches of 5 days data at a time or we will not get enough data points. Example call - https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=IBM&apikey=demo&topics=technology&time_from=20230320T0000&time_to=20230325T0000&limit=200. We are storing only 7 fields when creating the data frame -> Stock_Name(Name of the ticker), Stock(Ticker), Time(Time stamp when the article was published in UTC), Day(Date in day format), URL(Article URL), Title(Article title), Sentiment(Sentiment value) & Record_Count(1 for each record which will be used post data transformation for aggregation purposes).  

  - There is a limit of 5 calls per min to Alpha Vantage with the free key, so we have a pausing mechanism that will pause the execution for 60 secs + 2 secs (for buffer) after every 5 calls made. There is also a limit of 500 calls per day, so we must make sure not to breach that limit. Would be best to calculate how many calls would be required for the data fetch before doing a run. Example – if the stocks to pull data for is 5; The time period in weeks to pull the data for is 52 then total calls would be -> time series daily adjusted data(5 calls) + time series sentiment data(5*52 calls) = 265 calls. Since 265 is below the daily limit of 500, it is safe to move forward.   

  - **The upload_to_gcs** function is uploading our raw data and spark job python file from docker to the GCS bucket we created with Terraform.   

  - The **submit_spark_job** function is submitting the spark job python file from GCS to DataProc to transform raw data present in GCS and store/append it to our BQ DWH table. Refer *spark_job.py* for more details. I am joining stock data and stock sentiment data using an outer join so that I can visualise their correlation and identify individual articles if need be.  

- The dashboard is built on top of the BQ table.
  - Following fields are calculated to use in the dashboard :
    - Daily Adjusted Closing Value = SUM(Value)/COUNT(Value)  
      
    - Average Sentiment = SUM(Sentiment)/SUM(Record_Count)
    - Maximum Positive Sentiment = MAX(Sentiment)
    - Maximum Negative Sentiment = MIN(Sentiment).  
  - I have created 3 charts in the dashboard :
    - Day-on-day trend of daily adjust closing value and daily average sentiment for the selected stock. 
    - Day on day-on-day maximum positive and negative sentiment recorded for the selected stock. 
    - Table to identify topmost negative or positive articles.


## How to replicate 

### Step 0 - Get the following before starting to replicate.  
- Alpha Vantage API free key - https://www.alphavantage.co/support/#api-key.  
  
- GCP service account key(JSON) - Roles -> Owner - https://cloud.google.com/iam/docs/service-accounts-create and https://cloud.google.com/iam/docs/keys-create-delete. 
- Create a prefect cloud account, create a workspace and an API key - https://docs.prefect.io/ui/cloud-api-keys/.
- Install Docker - https://docs.docker.com/desktop/.

### Step 1 - Set up – Takes approximately 15 mins.  
- Download the entire folder/clone the repo.  
  
- Replace the dummy **gcp_key.json** file inside the codes folder with your own key. Make sure to rename it to gcp_key.json.  
- Start Docker desktop and open terminal in the folder containing your DockerFile.  
- Build Docker image.  
`docker build -t de_zc .`  
- Create container from image/start the container.   
`docker run -it --name de_zc_container de_zc`  
- *Going forward use this command to start the container.  
`docker start -i de_zc_container`  
- Install gcloud cli and authorize gcloud with browser. You’ll also need your GCP project ID handy to initialise gcloud. Note - Docker OS is Debian. https://cloud.google.com/sdk/docs/install#deb.  
- Install Terraform. https://developer.hashicorp.com/terraform/downloads. For installation choose Linux(Ubuntu/Debian).
- Connect to prefect cloud with your key.  
`prefect cloud login -k prefect_key`  
- Set environmental variable for GCP key  
`export GOOGLE_APPLICATION_CREDENTIALS=/app/codes/gcp_key.json`

### Step 2 - Create GCP resources with Terraform.  
- Navigate inside the codes folder.  
`cd codes`  
- Run following commands and follow instructions – **Change the variable names as per your set up**.  
`terraform init`    
`terraform plan -var="project_name=your_gcp_project_id" -var="region=your_region" -var="gcs_bucket_name=your_gcs_bucket_name" -var="bq_dataset_name=your_bq_dataset_name" -var="spark_cluster_name=your-spark-cluster-name"`    
`terraform apply -var="project_name=your_gcp_project_id" -var="region=your_region" -var="gcs_bucket_name=your_gcs_bucket_name" -var="bq_dataset_name=your_bq_dataset_name" -var="spark_cluster_name=your-spark-cluster-name"`    

### Step 3 - Build deployment and save it to cloud (Make sure you are connected to prefect cloud).  
- `python pipeline_deployment_build.py`  

### Step 4 - Run the pipeline  
- Go to prefect cloud to manage your runs. Your deployment ‘Data Pipeline Main Flow - DE ZC 2023’ should be created in the deployments section. Do a quick run and edit the parameters.  
  
- Parameters explanation here.  
  - "gcp_key_path”: "/app/codes/gcp_key.json" – Path to gcp key. You don’t need to change this.  
    
  - "alpha_vantage_key” : "alpha_vantage_api_key" – Your free Alpha Vantage API key.
  - "from_date” : "2021-12-27" – Starting date (**Monday** in YYYY-MM-DD format) to pull data from.
  - "to_date" : "2023-03-27" – Ending date (**Monday** in YYYY-MM-DD) to pull date until. 
  - "gcs_bucket_name" : "your_gcs_bucket_name" – GCS data lake bucket name you have set with terraform.
  - "bq_dataset_name” : "your_bq_dataset_name" – BQ dataset name you have set with terraform.
  - "bq_table_name” : "your_bq_table_name" – BQ table to store data in.
  - "spark_cluster_name” : "your-spark-cluster-name" – DataProc cluster name you have set with Terraform.
  - "spark_job_region” : " your_region" – Region you have set with Terraform.
  - "spark_job_file” : "spark_job.py" – Spark job python file. You don’t need to change this.  

- Start prefect agent in your docker container and wait for the flow run to start.  
`prefect agent start -q default`  
  
- Once the agent picks up the run, you can then monitor its progress in prefect clou.  

### Step 5(Optional) - Delete project.  
  
- Stop prefect agent with Control C.  
  
- Delete all GCP resources with Terraform – **Change the variable names as per your set up**.  
`terraform destroy -var="project_name=your_gcp_project_id" -var="region=your_region" -var="gcs_bucket_name=your_gcs_bucket_name" -var="bq_dataset_name=your_bq_dataset_name" -var="spark_cluster_name=your-spark-cluster-name"`    
  
- You will also need to delete the temp storage bucket created by the Dataproc cluster. This has to be done manually.   

- Exit from the container.  
`exit`  
  
- Delete container.   
`docker rm de_zc_container`  
  
- Delete image.  
`docker image rm de_zc`

## Dashboard and results 
- You can access the dashboard [here](https://lookerstudio.google.com/reporting/ac1aeee7-3fcf-4be6-b443-3977f59b8fe7). It is an exact copy of my official dashboard and created using my personal account to make it available for everyone to access. The official dashboard is [here](https://lookerstudio.google.com/s/nE0ODSDa_o8)(exactly the same) however the link is restricted and can only be shared on a case by case basis. Peer reviewers from DE ZC 2023 will have to make an access request using their google account. Please expect access within 1-2 days. You can also ping me on slack.  

![Dashboard Screenshot](https://user-images.githubusercontent.com/12958946/229422141-fc9ab605-6925-4f35-aef6-a352a03208a1.png)

  
- Findings  
  - It doesn't seem like there is a significant correlation between stock values and average sentiments recorded.  
    
  - Apple and ASML do show a positive correlation however it is only between 10-25% range. 
  - Google and Microsoft on the other hand are showing a negative correlation.  


- Further investigation 
  - Perhaps there is a delayed effect from the articles. We can apply time series day wise delay transformations to test correlations. It is possible the impact takes effect 1 or 2 days from the time the article was published. In the real world anyway it would take some time before an article or news becomes popular unless it is breaking news.


## Scope for improvement 
- The project considers only top 5 stocks by market cap. More stocks can be included in the project and bucketed into large, medium, and small and check if results are uniform across all.  
  
- Only technology stocks are considered in this project. Stocks from other sectors like retail, manufacturing, finance, real estate can also be investigated.  
- The project can be tweaked to gain granular level insights with near real time reporting by using intraday data & scheduling pipeline runs with Prefect every hour.

## Reviewing criteria  
- Problem description – *The problem statement and project description is defined [here](#problem-statement-and-project-description).*  
  
  - 0 points: Problem is not described
  - 1 point: Problem is described but shortly or not clearly
  - 2 points: Problem is well described and it's clear what the problem the project solves    
- Cloud – *GCP is used for data lake, data warehouse & dataproc cluster and is managed with Terraform.*
  - 0 points: Cloud is not used, things run only locally
  - 2 points: The project is developed in the cloud
  - 4 points: The project is developed in the cloud and IaC tools are used  
- Data ingestion (choose either batch or stream)  
  - Batch / Workflow orchestration – *Batch processing of end-to-end pipeline with tasks/flows defined in Prefect and Prefect cloud used for orchestrating runs.*
    - 0 points: No workflow orchestration
    - 2 points: Partial workflow orchestration: some steps are orchestrated, some run manually
    - 4 points: End-to-end pipeline: multiple steps in the DAG, uploading data to data lake
- Data warehouse – *Big Query Datawarehouse used to store transformed table. Please note for the sake of optimization, partitioning and clustering is not used for this project as we are not dealing with large size datasets. The final transformed data is in MBs and as discussed in lecture videos it doesn’t make to apply table partitioning and clustering in such cases. Reference to lecture - https://youtu.be/-CqXf7vhhDs?t=136*
  - 0 points: No DWH is used
  - 2 points: Tables are created in DWH, but not optimized
  - 4 points: Tables are partitioned and clustered in a way that makes sense for the upstream queries (with explanation)
- Transformations (dbt, spark, etc) – *Spark is used for data transformations.*
  - 0 points: No tranformations
  - 2 points: Simple SQL transformation (no dbt or similar tools)
  - 4 points: Tranformations are defined with dbt, Spark or similar technologies
- Dashboard – *Dashboard is created with Looker studio. 3 charts/tiles created.*
  - 0 points: No dashboard
  - 2 points: A dashboard with 1 tile
  - 4 points: A dashboard with 2 tiles
- Reproducibility – *Documentation written in detail to include project description, pipeline diagram, pipeline explanation, clear steps to reproduce along with summary of findings and notes on scope for improvement.*
  - 0 points: No instructions how to run code at all
  - 2 points: Some instructions are there, but they are not complete
  - 4 points: Instructions are clear, it's easy to run the code, and the code works
