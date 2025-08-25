import pandas as pd
from faker import Faker
from datetime import timedelta
from random import choice,randint

fake= Faker()
def generate_contract_data(vehicles_df, products_df, num_records=100):
    # Get actual IDs from the provided datasets
    vehicle_ids = vehicles_df["Vehicle ID"].tolist()
    product_ids = products_df["Product ID"].tolist()

    contracts = []
    data_records = []
    used_new_customers = set()
    existing_customer_pool = [fake.unique.random_int(min=1000, max=2000) for _ in range(100)]

    for i in range(1, num_records + 1):
        # Customer logic
        if randint(1, 100) <= 60:
            customer_id = choice(existing_customer_pool)
            existing_customer = "yes"
        else:
            while True:
                customer_id = fake.unique.random_int(min=2001, max=5000)
                if customer_id not in used_new_customers:
                    used_new_customers.add(customer_id)
                    break
            existing_customer = "no"

        # Lease info
        lease_start = fake.date_between(start_date="-2y", end_date="today")
        lease_term_months = choice([12, 24, 36, 48])
        lease_expiry = lease_start + timedelta(days=lease_term_months * 30)

        # Foreign key IDs picked from real tables
        vehicle_id = choice(vehicle_ids)
        product_id = choice(product_ids)

        # Build contract
        contract = {
            "Contract ID": i,
            "Customer ID": customer_id,
            "Existing Customer": existing_customer,
            "Vehicle ID": vehicle_id,   # FK → Vehicles
            "Product ID": product_id,   # FK → Products
            "Monthly EMI": randint(300, 1000),
            "Lease Start Date": lease_start,
            "Lease Expiry Date": lease_expiry,
            "Road Assistance": choice(["yes", "no"]),
            "Maintenance": choice(["yes", "no"]),
            "Discount Applied": "yes" if existing_customer == "yes" and randint(1,100) <= 30 else "no",
            "Preferred Customer": "yes" if existing_customer == "yes" and randint(1,100) <= 20 else "no"
        }
        contracts.append(contract)

        # Summary for vector DB
        summary = (
            f"Contract {i}: Lease of Vehicle {vehicle_id} under Product {product_id} "
            f"with Lease Start: {lease_start}, Expiry: {lease_expiry}, "
            f"EMI {contract['Monthly EMI']} USD, Road Assistance: {contract['Road Assistance']}, "
            f"Maintenance: {contract['Maintenance']}, Existing Customer: {existing_customer}, "
            f"Discount: {contract['Discount Applied']}"
        )

        data_records.append({
            "Summary": summary,
            "Contract ID": i,
            "Customer ID": customer_id,
            "Vehicle ID": vehicle_id,
            "Product ID": product_id
        })

    return pd.DataFrame(contracts), pd.DataFrame(data_records)

if __name__ == "__main__":
    num_records = 500
    vehicles_df = pd.read_csv("../data/vehicle_data.csv")
    products_df = pd.read_csv("../data/leasing_data.csv")
    df_contracts, customer_contract_data = generate_contract_data(num_records=num_records,vehicles_df=vehicles_df,products_df=products_df)
    df_contracts.to_csv("../data/contract_data.csv", index=False)
    customer_contract_data.to_csv("../data/customer_contract_data.csv", index=False)
    print(df_contracts.head())
    print(customer_contract_data.head())
