import pandas as pd
from faker import Faker
import random

fake= Faker()
percent_dict = {12:0.15,24:20,36:35,48:40}
def generate_quote_df(vehicle_data, product_data, n=20):
    quotes = []
    customer_pool = [f"{1000+i}" for i in range(1, 21)]  # 20 customers
    customer_ids = {}

    for i in range(n):
        quote_id = f"Q{i+1:04d}"
        customer_id = random.choice(customer_pool)
        existing_customer = "Yes" if customer_id in customer_ids else "No"

        vehicle = vehicle_data.sample(1).iloc[0]
        product = product_data.sample(1).iloc[0]   

        # Quote price & monthly EMI calulation
        lease_term = int(product["Lease Term"])
        base_price = vehicle["Price"]
        quote_price = base_price * percent_dict[int(lease_term)] #depreciation price of vehicle based on lease duration
        emi = round((quote_price / int(lease_term)) * random.uniform(1.05, 1.15), 2) 

        # Created date
        created_date = fake.date_between(start_date="-1y", end_date="today")
        
        # Discount
        discount = "Yes" if existing_customer == "Yes" and random.random() < 0.3 else "No"
        
        # Natural language summary
        summary = (
            f"Quote {quote_id} for {customer_id} leasing Vehicle {vehicle['Vehicle ID']} "
            f"under Product {product['Product ID']} with a monthly EMI of €{emi}. "
            f"Quote generated on {created_date}, Discount Applied: {discount}"
        )

        quote = {
            "Quote ID": quote_id,
            "User ID": customer_id,
            "Vehicle ID": vehicle["Vehicle ID"],
            "Product ID": product["Product ID"],
            "Monthly EMI": emi,
            "Quote Price" : quote_price,
            "Created Date": created_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Discount Applied": discount,
            "Summary": summary
        }

        quotes.append(quote)

        # Track customer contracts
        customer_ids[customer_id] = customer_ids.get(customer_id, 0) + 1

    df = pd.DataFrame(quotes)
    return df

if __name__ == "__main__":
    num_records = 50
    vehicles_df = pd.read_csv("../data/vehicle_data_new.csv")
    products_df = pd.read_csv("../data/leasing_data_new.csv")
    df_quotes = generate_quote_df(n=num_records,vehicle_data=vehicles_df,product_data=products_df)
    df_quotes.to_csv("../data/quote_data.csv", index=False)    
    quote_chunk_data = df_quotes[["Summary","Quote ID","Customer ID","Vehicle ID","Product ID"]]    
    quote_chunk_data.to_csv("../data/quote_chunk_data.csv",index=False)
    print(df_quotes.head())

"""
🔹 Logic for Realistic Quote Data

Quote ID → Unique (Q0001, Q0002 …).

Customer ID → Random (CUST-1234). Ensure some are Existing Customers.

Existing Customer → If repeat Customer ID, mark as "Yes", else "No".

Vehicle ID → Pick from Vehicle collection.

Product ID → Pick from Product collection (must match valid leasing plans).

Monthly EMI →

Derived from Vehicle.Price and Product.Lease Term.

Formula: EMI ≈ (Price / Lease Term) + 5–10% interest.

Lease Start Date → Random realistic past dates (2022–2025).

Lease Expiry Date → Start Date + Lease Term months.

Road Assistance → "Yes" if Maintenance Type = "Roadside" in product.

Maintenance → "Yes" if product includes garage/roadside services.

Discount Applied → "Yes" for loyal or existing customers (20–30% chance).

Preferred Customer → Mark "Yes" if contract is 2nd+ for same customer.
"""