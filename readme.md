# pandas-basics-project

#  Shopping Data Exploration & Cleaning using Pandas

A beginner-friendly Python project focused on **data exploration, cleaning, and preprocessing** using a real-world e-commerce shopping dataset from Kaggle. This project demonstrates essential **Pandas operations**, data handling techniques, and preprocessing workflows in **Google Colab**.

---

##  Project Overview

This project was created to practice the fundamentals of **Python for Data Analysis** by working with a real shopping dataset. The notebook covers the complete workflow from loading raw CSV data to generating a cleaned dataset ready for analysis.

---

## Features & Tasks Performed

- Loaded and explored a real-world e-commerce dataset
- Performed dataset inspection and statistical analysis
- Identified and handled missing values
- Cleaned inconsistent text-based price data
- Converted columns into appropriate data types
- Filtered rows based on conditions
- Selected and manipulated important columns
- Removed duplicate records
- Created derived/calculated columns
- Exported the cleaned dataset into CSV format

---

## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python 3 | Programming Language |
| Pandas | Data Analysis & Cleaning |
| NumPy | Numerical Operations |
| Google Colab | Development Environment |
| Kaggle Dataset | Data Source |

---

##  Project Structure

```bash
pandas-basics-project/
│
├── Shopping_Data_Exploration_Cleaning.ipynb
├── dresses.csv
├── shopping_cleaned.csv
└── README.md
```

---

##  Dataset Information

- **Dataset Source:** Kaggle Shopping Dataset
- **Type:** E-commerce Product Listings
- **Contains:** Product details, ratings, prices, discounts, seller information, categories, and reviews

### Example Dataset Columns

- Product ID
- Product Title
- Ratings
- Final Price
- Discount
- Seller Name
- Category
- Product Description

---

## 📖 Steps Covered

### 1️⃣ Import Libraries
Imported required libraries such as:
```python
import pandas as pd
import numpy as np
```

### 2️⃣ Load Dataset
Loaded CSV dataset into a Pandas DataFrame.

### 3️⃣ Data Exploration
Used:
- `head()`
- `tail()`
- `shape`
- `dtypes`
- `describe()`

to understand the dataset structure and statistics.

### 4️⃣ Missing Value Handling
- Checked null values using:
```python
df.isnull().sum()
```
- Filled missing values using `fillna()`.

### 5️⃣ Data Cleaning
- Removed unwanted symbols from price columns
- Converted text data into numeric format
- Fixed inconsistent formatting

### 6️⃣ Filtering & Selection
Performed conditional filtering and selected important columns for analysis.

### 7️⃣ Duplicate Removal
Removed duplicate rows using:
```python
df.drop_duplicates()
```

### 8️⃣ Feature Engineering
Created new calculated columns such as:
```python
total_amount = final_price * ratings_count
```

### 9️⃣ Export Cleaned Dataset
Saved the cleaned dataset into CSV format.

---

##  Key Pandas Concepts Used

- DataFrames
- CSV Handling
- Null Value Handling
- Data Type Conversion
- Conditional Filtering
- Column Selection
- Duplicate Removal
- Feature Engineering
- Data Exporting

---

##  Learning Outcomes

Through this project, I learned:
- Real-world dataset preprocessing
- Data cleaning workflows
- Core Pandas functions
- Handling inconsistent datasets
- Performing exploratory data analysis (EDA)



##  Author

**Basic Python & Pandas Learning Project**  
Developed as a beginner-level hands-on practice project for learning data analysis and preprocessing using Python.


