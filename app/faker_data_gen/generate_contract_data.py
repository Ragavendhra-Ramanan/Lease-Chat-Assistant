import pandas as pd
from faker import Faker
from datetime import timedelta
import random

fake= Faker()
def generate_contracts_df(vehicle_data, product_data, n=20):
    contracts = []
    customer_pool = [f"{1000+i}" for i in range(1, 21)]  # 20 customers
    customer_contracts = {}

    for i in range(n):
        contract_id = f"C{i+1:04d}"
        customer_id = random.choice(customer_pool)
        existing_customer = "Yes" if customer_id in customer_contracts else "No"

        vehicle = vehicle_data.sample(1).iloc[0]
        product = product_data.sample(1).iloc[0]

        # Lease term & EMI calculation
        lease_term = int(product["Lease Term"])
        base_price = vehicle["Price"]
        emi = round((base_price / lease_term) * random.uniform(1.05, 1.15), 2)

        # Start & expiry dates
        start_date = fake.date_between(start_date="-3y", end_date="today")
        expiry_date = start_date + timedelta(days=30 * lease_term)

        # Maintenance & assistance
        maintenance = "Yes" if product["Maintenance Type"] in ["Garage", "Roadside"] else "No"
        road_assist = "Yes" if product["Maintenance Type"] == "Roadside" else "No"

        # Discounts & Preferred
        discount = "Yes" if existing_customer == "Yes" and random.random() < 0.3 else "No"
        preferred = "Yes" if existing_customer == "Yes" else "No"

        # Natural language summary
        summary = (
            f"Contract {contract_id} for {customer_id} leasing Vehicle {vehicle['Vehicle ID']} "
            f"under Product {product['Product ID']} with a monthly EMI of €{emi}. "
            f"Lease runs from {start_date} to {expiry_date}. "
            f"Road Assistance: {road_assist}, Maintenance: {maintenance}, "
            f"Discount Applied: {discount}, Preferred Customer: {preferred}."
        )

        contract = {
            "Contract ID": contract_id,
            "Customer ID": customer_id,
            "Existing Customer": existing_customer,
            "Vehicle ID": vehicle["Vehicle ID"],
            "Product ID": product["Product ID"],
            "Monthly EMI": emi,
            "Lease Start Date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Lease Expiry Date": expiry_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Road Assistance": road_assist,
            "Maintenance": maintenance,
            "Discount Applied": discount,
            "Preferred Customer": preferred,
            "Summary": summary
        }

        contracts.append(contract)

        # Track customer contracts
        customer_contracts[customer_id] = customer_contracts.get(customer_id, 0) + 1

    df = pd.DataFrame(contracts)
    return df

if __name__ == "__main__":
    num_records = 500
    vehicles_df = pd.read_csv("../data/vehicle_data.csv")
    products_df = pd.read_csv("../data/leasing_data.csv")
    df_contracts = generate_contracts_df(n=num_records,vehicle_data=vehicles_df,product_data=products_df)
    df_contracts.to_csv("../data/contract_data.csv", index=False)
    print(df_contracts.head())

"""
🔹 Logic for Realistic Contract Data

Contract ID → Unique (C0001, C0002 …).

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