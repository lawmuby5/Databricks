# Databricks notebook source
# MAGIC %sql CREATE CATALOG IF NOT EXISTS ecommerce;
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG ecommerce;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Creating schemas because we are using medallion architecture
# MAGIC CREATE SCHEMA IF NOT EXISTS ecommerce.bronze;
# MAGIC CREATE SCHEMA IF NOT EXISTS ecommerce.silver;
# MAGIC CREATE SCHEMA IF NOT EXISTS ecommerce.gold;

# COMMAND ----------

# MAGIC %sql 
# MAGIC SHOW DATABASES FROM ecommerce;
# MAGIC      

# COMMAND ----------

# %sql 
# DROP CATALOG IF EXISTS ecommerce CASCADE; cascade drops all the info on catalog

# COMMAND ----------

