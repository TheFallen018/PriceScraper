import sqlite3

def fetch_all_products():
    # Connect to the SQLite database
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    # Execute a SQL query to select all records from the products table
    #cursor.execute('SELECT * FROM products WHERE title Like "%Pepsi%"')
    cursor.execute('SELECT * FROM products')


    # Fetch all the results
    products = cursor.fetchall()

    # Close the database connection
    conn.close()

    return products

# Fetch and print all products
all_products = fetch_all_products()
for product in all_products:
    print(product)