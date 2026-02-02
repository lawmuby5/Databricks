# Databricks notebook source
# MAGIC %md
# MAGIC ### Ingest Fact Data into Bronze Layer

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType, BooleanType
import pyspark.sql.functions as F

# COMMAND ----------

catalog_name = 'ecommerce'

# COMMAND ----------

order_items_schema = StructType([
    StructField("dt",                 StringType(), True),
    StructField("order_ts",           StringType(), True),
    StructField("customer_id",        StringType(), True),
    StructField("order_id",           StringType(), True),
    StructField("item_seq",           StringType(), True),
    StructField("product_id",         StringType(), True),
    StructField("quantity",           StringType(), True),
    StructField("unit_price_currency",StringType(), True),
    StructField("unit_price",         StringType(), True),
    StructField("discount_pct",       StringType(), True),
    StructField("tax_amount",         StringType(), True),
    StructField("channel",            StringType(), True),
    StructField("coupon_code",        StringType(), True),
])

# COMMAND ----------

# Load data using the schema defined
raw_data_path = "/Volumes/ecommerce/source_data_/raw/order_items/landing/*.csv"


df = spark.read.option("header", "true").option("delimiter", ",").schema(order_items_schema).csv(raw_data_path) \
    .withColumn("file_name", F.col("_metadata.file_path")) \
    .withColumn("ingest_timestamp", F.current_timestamp())

# COMMAND ----------

# DBTITLE 1,Untitled
display(df.limit(5))

# COMMAND ----------

df.count()

# COMMAND ----------

df.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.bronze.brz_order_items")

# COMMAND ----------

# MAGIC %md
# MAGIC This notebook helps to do the final cleaning of the data in a way that suits the stakeholders request, we had to utilise the order table as it is thge main thing we needed to know, so we created the order table into the fact bronze folder and from there we continued the emediallion architecture
# MAGIC

# COMMAND ----------

