import pandas as pd
from faker import Faker
from datetime import datetime
from random import choice
from faker.providers import DynamicProvider

# Vehicle Makers
makers_list_provider = DynamicProvider(
    provider_name="vehicle_makers",
    elements=["Toyota", "Volkswagen", "Hyundai", "Honda", "Maruti Suzuki", "Tata Motors", "Mahindra"]
)

# Vehicle Model Types
model_type_provider = DynamicProvider(
    provider_name="vehicle_model",
    elements=["Sedan", "Hatchback", "SUV"]
)

fake = Faker()
fake.add_provider(makers_list_provider)
fake.add_provider(model_type_provider)

def generate_leasing_data(num_records=50):
    data_records = []
    for i in range(num_records):
        make = fake.vehicle_makers()
        model = fake.vehicle_model()        
        lease_term = choice(["12 months", "24 months", "36 months", "48 months", "60 months"])
        flexi = choice(["Yes", "No"])
        tax_plan = choice(["Yes", "No"])
        renewal = choice(["Monthly", "Quarterly", "Yearly"])
        maintenance = choice(["Roadside", "Garage"])

        product_name = f"{make} {model} Lease Plan"
        description = (
            f"{lease_term} {model.lower()} lease from {make} "
            f"with {'flexible terms' if flexi=='Yes' else 'standard terms'}, "
            f"{'tax saving benefits' if tax_plan=='Yes' else 'no tax saving plan'}, "
            f"and {maintenance.lower()} support."
        )

        record = {
            "Product ID": f"P{1000+i}",  
            "Product Name": product_name,  
            "Short Description": description,
            "Lease Term": lease_term,
            "Flexi Lease": flexi,
            "Tax Saving Plan": tax_plan,
            "Renewal Cycle": renewal,
            "Maintenance Type": maintenance,
            "Inserted Date": fake.date_between_dates(
                date_start=datetime(2022, 1, 1), 
                date_end=datetime(2025, 8, 1)
            )
        }
        data_records.append(record)

    df = pd.DataFrame(data_records)

    # Add concatenated text column
    df["Summary"] = df.apply(
        lambda row: (
            f"Product Name: {row['Product Name']}, "
            f"Description: {row['Short Description']}, "
            f"Lease Term: {row['Lease Term']}, "
            f"Flexi Lease: {row['Flexi Lease']}, "
            f"Tax Saving Plan: {row['Tax Saving Plan']}, "
            f"Renewal Cycle: {row['Renewal Cycle']}, "
            f"Maintenance Type: {row['Maintenance Type']}, "
            f"Inserted Date: {row['Inserted Date']}"
        ), axis=1
    )

    return df,df[["Product ID", "Summary"]]  # final compact df with ID + text

if __name__ == "__main__":
    num_records = 50
    leasing_data, leasing_chunk_data = generate_leasing_data(num_records)
    leasing_data.to_csv("../data/leasing_data.csv", index=False)
    leasing_chunk_data.to_csv("../data/leasing_chunk_data.csv",index=False)
    print(leasing_data.head())
