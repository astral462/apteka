# Pharmacy App 💊

## About the Project

**Pharmacy App** is a desktop application built with Python that allows users to search for medicines, view product information, filter results by price, and process sales. The application has a Ukrainian-language interface and uses a green-and-white design.

The project uses CustomTkinter for the graphical user interface and PostgreSQL for storing and managing medicine and sales data.

## Features

- **Medicine Search** — Search for medicines by product name, active ingredients, manufacturer, or related diseases.
- **Symptom Search** — Select or enter symptoms to find relevant medicines in the database.
- **Medicine Details** — View product descriptions, prices, availability, manufacturers, active ingredients, dosage, contraindications, and prescription requirements.
- **Price Filtering** — Filter medicines by minimum and maximum price.
- **Sorting** — Sort search results by price, from lowest to highest or highest to lowest.
- **Shopping Cart** — Add medicines to the cart and remove them before checkout.
- **Customer Search** — Find customer information using a phone number.
- **Payment Methods** — Select cash, card, or terminal as the payment method.
- **Receipt Generation** — Create a receipt containing the receipt number, date, customer details, purchased items, payment method, and total price.
- **Stock Management** — Update stock quantities and sales information when a purchase is completed.
- **Database Integration** — Store medicine information and sales receipts in PostgreSQL.

## Technologies Used

- **Python** — Main programming language.
- **CustomTkinter** — Desktop graphical user interface.
- **PostgreSQL** — Relational database for medicine information and sales records.
- **psycopg2** — Python library for connecting to PostgreSQL.
- **Redis** — Redis client initialization is included in the code; additional functionality depends on the implementation.

## Requirements

Before running the application, install Python and the required libraries.

Install the dependencies using:

```bash
pip install customtkinter psycopg2-binary redis
```

The application also requires access to a PostgreSQL database containing the `pharmacy` table.

A running Redis server is required if Redis functionality is used.

## Installation and Setup

### 1. Clone or download the project

Download the project files to your computer and open the project folder in PyCharm or another Python IDE.

### 2. Install dependencies

Open the terminal in your project directory and run:

```bash
pip install customtkinter psycopg2-binary redis
```

### 3. Configure the database

Configure the PostgreSQL connection in the Python code with your database host, port, username, password, and database name.

For security, store database credentials in environment variables rather than directly in the source code.

The database must contain a `pharmacy` table with the medicine and sales columns used by the application.

The application attempts to create two additional tables automatically:

- `pharmacy_receipts` — Stores receipt information.
- `pharmacy_receipt_items` — Stores the individual items included in each receipt.

The database user needs the appropriate permissions to create and update these tables.

### 4. Configure Redis

The code initializes a connection to a Redis server running locally on port `6379`. If Redis is required by your setup, make sure the Redis server is running and configure the connection as needed.

### 5. Run the application

Run the main Python file:

```bash
python main.py
```

Replace `main.py` with the actual name of your Python file.

## Database Structure

### `pharmacy`

Contains medicine information and sales-related data, including:

- Product ID and name
- Category and description
- Manufacturer and country
- Price and stock quantity
- Diseases and active ingredients
- Dosage and contraindications
- Prescription requirements
- Sale date and payment information

### `pharmacy_receipts`

Stores completed sales, including:

- Unique receipt number
- Sale date
- Customer name and phone number
- Payment method
- Total amount

### `pharmacy_receipt_items`

Stores the items associated with each receipt, including:

- Receipt ID
- Product ID and name
- Quantity
- Unit price
- Total item price

## How to Use

1. Launch the application.
2. Search for a medicine by name or enter symptoms.
3. Select symptoms using the available buttons if needed.
4. Click **Пошук** to display the results.
5. Apply price filters or change the sorting option.
6. Open **Деталі** to view additional medicine information.
7. Click **В кошик** to add a medicine to the cart.
8. Open the cart and review the selected products.
9. Enter customer information if required.
10. Select the payment method and enter the amount received when applicable.
11. Click **Оформити продаж та створити чек** to complete the sale.
12. Review the generated receipt.

## Project Purpose

This project demonstrates the development of a Python desktop application with a graphical user interface, database integration, search functionality, filtering, sorting, shopping cart management, and sales processing.

It combines several programming concepts, including object-oriented programming, SQL queries, database transactions, event-driven interfaces, and data management.

## Notes

- The application interface is written in Ukrainian.
- Medicine data must be available in the PostgreSQL database before it can be searched.
- Receipt tables are created automatically when the application starts, provided the database permissions allow it.
- Redis is initialized in the provided code, but a specific Redis-based feature is not fully demonstrated.
- This application is a software project and should not be used as a substitute for professional medical advice.

## Author

Developed as a Python programming project.
