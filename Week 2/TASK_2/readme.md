# E-Commerce Sales Database

A SQL-based database project that simulates an e-commerce platform by managing customers, products, orders, and order details. This project demonstrates database design, relational modeling, query optimization, data analysis, and transaction management using MySQL.

## Objectives

* Design a normalized relational database schema.
* Implement primary and foreign key relationships.
* Perform data retrieval, filtering, and aggregation.
* Analyze business data using SQL queries.
* Apply indexing and transaction management concepts.

---

## Database Schema

The database consists of four interconnected tables:

### Customers

Stores customer details including name, email, location, join date, and membership status.

### Products

Maintains product information such as category, brand, pricing, and stock availability.

### Orders

Records customer purchases along with order status and total transaction amount.

### Order_Items

Stores item-level details for each order including quantity, price, and discount information.

---

## Entity Relationship Diagram

```text
Customers
    │
    │ 1:N
    ▼
Orders
    │
    │ 1:N
    ▼
Order_Items
    ▲
    │ N:1
Products
```

---

## Key SQL Concepts Implemented

### Database Design

* CREATE DATABASE
* CREATE TABLE
* Primary Keys
* Foreign Keys
* UNIQUE Constraints
* CHECK Constraints

### Data Retrieval

* SELECT
* DISTINCT
* ORDER BY
* LIMIT

### Filtering

* WHERE Clause
* BETWEEN
* IN
* LIKE
* Date-based Filtering

### Aggregation

* COUNT()
* SUM()
* AVG()
* MIN()
* MAX()
* GROUP BY
* HAVING

### Joins

* INNER JOIN
* LEFT JOIN
* RIGHT JOIN
* Multi-table JOINs

### Advanced SQL

* CASE Statements
* Transactions
* COMMIT
* ROLLBACK
* ACID Properties

### Performance Optimization

* Index Creation
* Query Optimization Techniques
* Efficient Filtering Strategies

---

## Project Structure

```bash
.
├── ecommerce_sales_database.sql
├── answers.md
└── README.md
```

---

## Files Description

### ecommerce_sales_database.sql

Contains:

* Database creation scripts
* Table definitions
* Constraints
* Index creation
* Sample data insertion

### answers.md

Contains:

* SQL query solutions
* Filtering and optimization queries
* Aggregation queries
* Join operations
* Advanced SQL concepts

---

## Learning Outcomes

Through this project, I gained practical experience in:

* Relational Database Design
* SQL Query Development
* Data Modeling
* Business Data Analysis
* Query Optimization
* Database Constraints
* Transaction Handling
* Reporting and Analytics

---

## Technologies Used

* MySQL 8.0
* MySQL Workbench
* SQL

---

## Author

**Muskan Goyal**
Data Engineering Intern | Celebal Technologies
