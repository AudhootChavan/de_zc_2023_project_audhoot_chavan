#Import libraries
from pyspark.sql import SparkSession
from pyspark.sql import types
import argparse


#Define parameters to pass for the main script
#Initiate parser
parser = argparse.ArgumentParser(description='Parameters for main script')
#Define arguments
parser.add_argument('--from_date', type=str, help='Starting date for the data fetch. Pass a Monday date. -> YYYY-MM-DD.', required=True)
parser.add_argument('--to_date', type=str, help='Ending date for the data fetch. Pass a Monday date. -> YYYY-MM-DD.', required=True)
parser.add_argument('--gcs_bucket_name', type=str, help='GCS bucket name that will be used to store raw data/as a staging area.', required=True)
parser.add_argument('--bq_dataset_name', type=str, help='Dataset in BQ to store table.', required=True)
parser.add_argument('--bq_table_name', type=str, help='Table name to store output from Spark.', required=True)
#Capture arguments as variables
args = parser.parse_args()
from_date = args.from_date
to_date = args.to_date
gcs_bucket_name = args.gcs_bucket_name
bq_dataset_name = args.bq_dataset_name
bq_table_name = args.bq_table_name

#Initialize spark session
spark = SparkSession.builder \
  .appName('DE ZC App')\
  .config('spark.jars', 'gs://spark-lib/bigquery/spark-bigquery-latest_2.12.jar') \
  .getOrCreate()
#Configure temporary bucket
spark.conf.set('temporaryGcsBucket', gcs_bucket_name)

#Set Schema for dataframes
stock_sentiment_df_schema = types.StructType([
    types.StructField('Stock_Name',types.StringType(),True),
    types.StructField('Stock',types.StringType(),True),
    types.StructField('Time',types.StringType(),True),
    types.StructField('Day',types.DateType(),True),
    types.StructField('URL',types.StringType(),True),
    types.StructField('Title',types.StringType(),True),
    types.StructField('Sentiment',types.FloatType(),True),
    types.StructField('Record_Count',types.IntegerType(),True)
    ])
stock_df_schema = types.StructType([
    types.StructField('Stock_Name',types.StringType(),True),
    types.StructField('Stock',types.StringType(),True),
    types.StructField('Day',types.DateType(),True),
    types.StructField('Value',types.FloatType(),True)
    ])

#Read raw data
stock_df = spark.read.option('header','true').schema(stock_df_schema).csv('gs://' + gcs_bucket_name + '/stocks_df_' + from_date + '_' + to_date + '.csv')
stock_sentiment_df = spark.read.option('header','true').schema(stock_sentiment_df_schema).csv('gs://' + gcs_bucket_name + '/stocks_sentiment_df_' + from_date + '_' + to_date + '.csv')
#Join the dataframes with outer join
df = stock_df.join(stock_sentiment_df,on=['Day', 'Stock', 'Stock_Name'],how='outer')
#Fill NA values with 0
df = df.fillna(0)
# For certain dates stock data is not available - So we will remove those dates
df = df.filter(df.Value > 0)
# Saving the data to BigQuery
df.write.format('bigquery') \
  .option('table', bq_dataset_name + '.' + bq_table_name) \
  .mode('append')\
  .save()