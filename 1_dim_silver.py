# Databricks notebook source
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType, TimestampType, FloatType
import pyspark.sql.functions as F

catalog_name  = 'ecommerce'

# COMMAND ----------

df_bronze = spark.table(f'{catalog_name}.bronze.brz_brands')
df_bronze.show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC

# COMMAND ----------

# MAGIC %md
# MAGIC Trimming data to take away the inconsistent spacing
# MAGIC

# COMMAND ----------

df_silver = df_bronze.withColumn("brand_name", F.trim(F.col("brand_name")))
df_silver.show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC CREATING A CODE TO HELP REPLACE THE CHARACTERS THAT ARE NOT ALPHANUMERIC USING REGEX

# COMMAND ----------

df_silver = df_silver.withColumn("brand_code", F.regexp_replace(F.col("brand_code"), r'[^A-Za-z0-9]', ''))
df_silver.show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC lOOKING AT THE CATEGORIES CODE ANOMALIES TO KNOW HOW TO FIX

# COMMAND ----------

df_silver.select("category_code").distinct().show()

# COMMAND ----------

# MAGIC %md
# MAGIC CODE TO STANDARDISE THE CODES AS BOOKS AND GROCERY WERE REPEATING AND NOT IN THE STANDARD FORMAT

# COMMAND ----------

# Anomalies dictionary
anomalies = {
    "GROCERY": "GRCY",
    "BOOKS": "BKS",
    "TOYS": "TOY"
}

# PySpark replace is easy
df_silver = df_silver.replace(to_replace=anomalies, subset=["category_code"])

# ✅ Show results
df_silver.select("category_code").distinct().show()

# COMMAND ----------

# Write raw data to the silver layer (catalog: ecommerce, schema: silver, table: slv_brands)
df_silver.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.silver.slv_brands")

# COMMAND ----------

# MAGIC %md 
# MAGIC CATEGORY 

# COMMAND ----------

df_bronze = spark.table(f"{catalog_name}.bronze.brz_category")

df_bronze.show(10)

# COMMAND ----------

df_duplicates = df_bronze.groupBy("category_code").count().filter(F.col("count") > 1)
display(df_duplicates)

# COMMAND ----------

df_silver = df_bronze.dropDuplicates(['category_code'])
display(df_silver)

# COMMAND ----------

df_silver = df_silver.withColumn("category_code", F.upper(F.col("category_code")))
display(df_silver)

# COMMAND ----------

# Write raw data to the silver layer (catalog: ecommerce, schema: silver, table: slv_category)
df_silver.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.silver.slv_category")

# COMMAND ----------

# MAGIC %md
# MAGIC products
# MAGIC

# COMMAND ----------

# Read the raw data from the bronze table (ecommerce.bronze.brz_calendar)
df_bronze = spark.read.table(f"{catalog_name}.bronze.brz_products")

# Get row and column count
row_count, column_count = df_bronze.count(), len(df_bronze.columns)

# Print the results
print(f"Row count: {row_count}")
print(f"Column count: {column_count}")

# COMMAND ----------

display(df_bronze.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC Check weight_grams (contains 'g')

# COMMAND ----------

# Check weight_grams column
df_bronze.select("weight_grams").show(5, truncate=False)

# COMMAND ----------

# replace 'g' with ''
df_silver = df_bronze.withColumn(
    "weight_grams",
    F.regexp_replace(F.col("weight_grams"), "g", "").cast(IntegerType())
)
df_silver.select("weight_grams").show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC Check `length_cm` (comma instead of dot)

# COMMAND ----------

df_silver.select("length_cm").show(3)

# COMMAND ----------

# replace , with .
df_silver = df_silver.withColumn(
    "length_cm",
    F.regexp_replace(F.col("length_cm"), ",", ".").cast(FloatType())
)
df_silver.select("length_cm").show(3)

# COMMAND ----------

df_silver.select("category_code", "brand_code").show(2)

# COMMAND ----------

# convert category_code and brand_code to upper case
df_silver = df_silver.withColumn(
    "category_code",
    F.upper(F.col("category_code"))
).withColumn(
    "brand_code",
    F.upper(F.col("brand_code"))
)
df_silver.select("category_code", "brand_code").show(2)

# COMMAND ----------



# COMMAND ----------

# MAGIC %md
# MAGIC Spelling mistakes in `material` column
# MAGIC
# MAGIC

# COMMAND ----------

df_silver.select("material").distinct().show()

# COMMAND ----------

# Fix spelling mistakes
df_silver = df_silver.withColumn(
    "material",
    F.when(F.col("material") == "Coton", "Cotton")
     .when(F.col("material") == "Alumium", "Aluminum")
     .when(F.col("material") == "Ruber", "Rubber")
     .otherwise(F.col("material"))
)
df_silver.select("material").distinct().show()    

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC
# MAGIC Negative values in rating_count
# MAGIC

# COMMAND ----------

df_silver.filter(F.col('rating_count')<0).select("rating_count").show(3)

# COMMAND ----------

# Convert negative rating_count to positive
df_silver = df_silver.withColumn(
    "rating_count",
    F.when(F.col("rating_count").isNotNull(), F.abs(F.col("rating_count")))
     .otherwise(F.lit(0))  # if null, replace with 0
)

# COMMAND ----------

# Check final cleaned data

df_silver.select(
    "weight_grams",
    "length_cm",
    "category_code",
    "brand_code",
    "material",
    "rating_count"
).show(10, truncate=False)

# COMMAND ----------

# Write raw data to the silver layer (catalog: ecommerce, schema: silver, table: slv_dim_products)
df_silver.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.silver.slv_products")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Customers

# COMMAND ----------

# Read the raw data from the bronze table (ecommerce.bronze.brz_calendar)
df_bronze = spark.read.table(f"{catalog_name}.bronze.brz_customers")

# Get row and column count
row_count, column_count = df_bronze.count(), len(df_bronze.columns)

# Print the results
print(f"Row count: {row_count}")
print(f"Column count: {column_count}")

df_bronze.show(10)

# COMMAND ----------

# MAGIC %md
# MAGIC %md
# MAGIC Handle NULL values in `customer_id` column

# COMMAND ----------

null_count = df_bronze.filter(F.col("customer_id").isNull()).count()
null_count

# COMMAND ----------

# There are 300 null values in customer_id column. Display some of those
df_bronze.filter(F.col("customer_id").isNull()).show(3)

# COMMAND ----------

# Drop rows where 'customer_id' is null
df_silver = df_bronze.dropna(subset=["customer_id"])

# Get row count
row_count = df_silver.count()
print(f"Row count after droping null values: {row_count}")

# COMMAND ----------

# MAGIC %md
# MAGIC Handle NULL values in `phone` column
# MAGIC

# COMMAND ----------

null_count = df_silver.filter(F.col("phone").isNull()).count()
print(f"Number of nulls in phone: {null_count}") 

# COMMAND ----------

df_silver.filter(F.col("phone").isNull()).show(3)

# COMMAND ----------

### Fill null values with 'Not Available'
df_silver = df_silver.fillna("Not Available", subset=["phone"])

# sanity check (If any nulls still exist)
df_silver.filter(F.col("phone").isNull()).show()

# COMMAND ----------

# Write raw data to the silver layer (catalog: ecommerce, schema: silver, table: slv_customers)
df_silver.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.silver.slv_customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Calendar/Date

# COMMAND ----------

# Read the raw data from the bronze table (ecommerce.bronze.brz_calendar)
df_bronze = spark.read.table(f"{catalog_name}.bronze.brz_calendar")

# Get row and column count
row_count, column_count = df_bronze.count(), len(df_bronze.columns)

# Print the results
print(f"Row count: {row_count}")
print(f"Column count: {column_count}")

df_bronze.show(3)

# COMMAND ----------

df_bronze.printSchema()

# COMMAND ----------

# MAGIC %md
# MAGIC Converting String to Date

# COMMAND ----------

from pyspark.sql.functions import to_date


# Convert the string column to a date type
df_silver = df_bronze.withColumn("date", to_date(df_bronze["date"], "dd-MM-yyyy"))

# COMMAND ----------

print(df_silver.printSchema())

df_silver.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC Remove Duplicates

# COMMAND ----------

# Find duplicate rows in the DataFrame
duplicates = df_silver.groupBy('date').count().filter("count > 1")

# Show the duplicate rows
print("Total duplicated Rows: ", duplicates.count())
display(duplicates)

# COMMAND ----------

# Remove duplicate rows
df_silver = df_silver.dropDuplicates(['date'])

# Get row count
row_count = df_silver.count()

print("Rows After removing Duplicates: ", row_count)

# COMMAND ----------

# Capitalize first letter of each word in day_name
df_silver = df_silver.withColumn("day_name", F.initcap(F.col("day_name")))

df_silver.show(5)

# COMMAND ----------

# MAGIC %md
# MAGIC Convert negative `week_of_year` to positive

# COMMAND ----------

df_silver = df_silver.withColumn("week_of_year", F.abs(F.col("week_of_year")))  # Convert negative to positive

df_silver.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC Enhance quarter and week_of_year column

# COMMAND ----------

df_silver = df_silver.withColumn("quarter", F.concat_ws("", F.concat(F.lit("Q"), F.col("quarter"), F.lit("-"), F.col("year"))))

df_silver = df_silver.withColumn("week_of_year", F.concat_ws("-", F.concat(F.lit("Week"), F.col("week_of_year"), F.lit("-"), F.col("year"))))

df_silver.show(3)

# COMMAND ----------

# MAGIC %md
# MAGIC Rename columns

# COMMAND ----------

# Rename a column
df_silver = df_silver.withColumnRenamed("week_of_year", "week")


# COMMAND ----------

# Write raw data to the silver layer (catalog: ecommerce, schema: silver, table: slv_calendar)
df_silver.write.format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .saveAsTable(f"{catalog_name}.silver.slv_calendar")

# COMMAND ----------

