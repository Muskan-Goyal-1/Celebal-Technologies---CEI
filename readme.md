# pandas-basics-project
# Basic Python Project — Shopping Data Exploration & Cleaning

A beginner-friendly Python project that demonstrates how to load, explore, clean, and analyse a real e-commerce shopping dataset using **Pandas** in Google Colab.

---

##  Project Objective

Learn Python basics and perform data exploration and cleaning using the Pandas library on a real-world Kaggle shopping dataset.

---

##  Project Files

| File | Description |
|------|-------------|
| `Shopping_Data_Exploration_Cleaning.ipynb` | Main Jupyter Notebook with all steps |
| `dresses.csv` | Raw dataset downloaded from Kaggle |
| `shopping_cleaned.csv` | Final cleaned dataset (output) |
| `README.md` | Project documentation (this file) |

---

##  Dataset

- **Source:** [Kaggle — Shopping Dataset by Anvitkumar](https://www.kaggle.com/datasets/anvitkumar/shopping-dataset)
- **Description:** E-commerce product listings with prices, ratings, seller info, discounts, and categories

### Columns in the Dataset

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | int | Unique product identifier |
| `title` | text | Product name |
| `product_description` | text | Full product description |
| `rating` | float | Average customer rating (0–5) |
| `ratings_count` | int | Number of customer ratings |
| `initial_price` | float | Original price before discount |
| `discount` | float | Discount amount (0 if no discount) |
| `final_price` | float | Price after discount applied |
| `currency` | text | Currency of the price |
| `category` | text | Product category |
| `seller_name` | text | Name of the seller |
| `seller_information` | text | Seller details |
| `sizes` | text | Available sizes |
| `variations` | text | Product variations |
| `what_customers_said` | text | Customer review snippets |
| `videos` | text | Product video links |
| `images` | text | Product image links |
| `best_offer` | text | Best offer available |
| `more_offers` | text | Additional offers |
| `delivery_options` | text | Shipping/delivery info |
| `breadcrumbs` | text | Navigation path on website |
| `product_details` | text | Extra product details |
| `product_specifications` | text | Technical specifications |
| `amount_of_stars` | text | Star breakdown |

---

## 🛠️ Tools & Libraries Used

| Tool | Purpose |
|------|---------|
| Python 3 | Programming language |
| Pandas | Data manipulation and cleaning |
| NumPy | Numerical operations |
| Google Colab | Cloud-based notebook environment |



## Steps Covered in the Notebook

### Step 0 — Import Libraries
```python
import pandas as pd
import numpy as np
```
Load the tools needed before starting any work.

---

### Step 1 — Load the Dataset
```python
df = pd.read_csv('shopping_dataset.csv')
```
Read the CSV file into a Pandas DataFrame (a table with rows and columns).

---

### Step 2 — Explore the Data
```python
df.head()        # First 5 rows
df.tail()        # Last 5 rows
df.shape         # Number of rows and columns
df.dtypes        # Data type of each column
df.describe()    # Statistical summary
```
Get familiar with the dataset — its size, structure, and basic statistics.

---

### Step 3a — Identify Missing Values
```python
df.isnull().sum()
```
Count how many blank/empty cells exist in each column.

**Missing values found:**

| Column | Missing Count |
|--------|--------------|
| `discount` | 121 |
| `what_customers_said` | 573 |
| `seller_name` | 301 |
| `seller_information` | 301 |
| `variations` | 562 |
| `videos` | 781 |

---

### Step 3b — Fill Missing Values
```python
df['discount'] = df['discount'].fillna(0)
df['seller_name'] = df['seller_name'].fillna('Not Available')
```
Fill blank cells with sensible default values so no column has empty gaps.

---

### Step 3c — Fix final_price Column
```python
df['final_price'] = (df['final_price']
                     .str.replace('"', '')
                     .str.replace('₹', '')
                     .str.replace(',', '')
                     .astype(float))
```
The `final_price` column was stored as text like `"₹3,995.00"`. Strip the symbols and convert to a real number so math can be done on it.

---

### Step 4 — Filter Rows & Select Columns
```python
# Filter rows
high_rated = df[df['rating'] >= 4]
discounted = df[df['discount'] > 0]

# Select columns
selected = df[['title', 'category', 'final_price', 'rating']]
```
Filter the data to show only rows matching a condition, and select only the columns you need.

---

### Step 5 — Remove Duplicates
```python
df = df.drop_duplicates().reset_index(drop=True)
```
Find and remove any rows that are exact copies of another row.

---

### Step 6 — Create a Derived Column
```python
df['total_amount'] = (df['final_price'] * df['ratings_count']).round(2)
```
Create a new column calculated from existing columns.
> Note: The original task asked for `price × quantity`. Since this dataset has no `quantity` column, `ratings_count` is used as the closest equivalent representing volume.

---

### Step 7 — Save the Cleaned Dataset
```python
df.to_csv('shopping_cleaned.csv', index=False)

from google.colab import files
files.download('shopping_cleaned.csv')
```
Save all your cleaned data to a new CSV file and download it.

---

##  Before vs After Cleaning

| | Raw Dataset | Cleaned Dataset |
|--|-------------|-----------------|
| Missing values | 2,639 | 0 |
| Duplicates | Present | 0 |
| `final_price` type | Text ❌ | Number ✅|
| Total columns | 24 | 25 |
| New column added | — | `total_amount` ✅ |

---

## Key Pandas Functions Learned

| Function | What It Does |
|----------|-------------|
| `pd.read_csv()` | Load a CSV file |
| `df.head()` / `df.tail()` | Preview first/last rows |
| `df.shape` | Get number of rows and columns |
| `df.dtypes` | Check data types of each column |
| `df.describe()` | Statistical summary |
| `df.isnull().sum()` | Count missing values |
| `df['col'].fillna(value)` | Fill missing values |
| `df[df['col'] > x]` | Filter rows by condition |
| `df[['col1', 'col2']]` | Select specific columns |
| `df.drop_duplicates()` | Remove duplicate rows |
| `df['new_col'] = expression` | Create a new derived column |
| `df.to_csv()` | Save DataFrame to CSV |

---

## Common Errors & Fixes

### TypeError: unsupported operand type — 'int' and 'str'
**Cause:** Trying to do math on a text column (e.g. `"₹3,995.00"`)
**Fix:** Strip symbols and convert to float using `.str.replace()` and `.astype(float)`

### ValueError: could not convert string to float
**Cause:** Hidden quote characters inside the string (e.g. `'"3995.00"`)
**Fix:** Add `.str.replace('"', '')` before `.astype(float)`

---

##  Author

**Project:** Basic Python & Pandas Learning Project
**Dataset:** [Kaggle — Shopping Dataset](https://www.kaggle.com/datasets/anvitkumar/shopping-dataset)
**Environment:** Google Colab (Python 3)
