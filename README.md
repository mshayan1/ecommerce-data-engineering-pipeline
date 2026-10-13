E-Commerce Data Engineering Pipeline

 Project Overview

This project demonstrates an end-to-end ETL pipeline using the Brazilian E-Commerce Public Dataset by Olist.

The pipeline extracts e-commerce data from CSV files, transforms and validates the data using Python and Pandas, and loads the processed records into a PostgreSQL database hosted on Neon.

 Technologies Used

- Python
- Pandas
- PostgreSQL
- Neon
- SQL
- GitHub

Pipeline Architecture

1. Extract:Read raw e-commerce CSV files.
2. Transform: Clean timestamps, standardize text, and inspect data quality.
3. Load: Store processed orders, customers, and products in PostgreSQL.
4. Validate: Check record counts and query the stored data.

Datasets

- Orders: 99,441 records
- Customers: 99,441 records
- Products: 32,951 records

These are the initial dataset sizes observed during development.

Current Status

- CSV extraction and inspection completed
- Initial data cleaning implemented
- PostgreSQL tables loaded and queried
- Initial reusable ETL script created

Automated scheduling, comprehensive testing, and production-grade error handling remain future improvements.

 Security

Database credentials should be stored in environment variables or a secrets manager. Never commit passwords or connection strings to the repository.

 Dataset Source

Olist Brazilian E-Commerce Public Dataset:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
