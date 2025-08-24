import pandas as pd
from faker import Faker
from faker.providers import DynamicProvider
from datetime import datetime, timedelta
from random import choice,randint

makers_list_provider = DynamicProvider(
     provider_name="vehicle_makers",
     elements=["Toyota", "Volkswagen", "Hyundai", "Honda", "Maruti Suzuki", "Tata Motors", "Mahindra"]
)

model_type_provider = DynamicProvider(
     provider_name="vehicle_model",
     elements=["Sedan","Hatchback","SUV"]
)

fuel_type_provider = DynamicProvider(
     provider_name="vehicle_fuel",
     elements=["Petrol","Diesel","EV"]
)

gear_type_provider = DynamicProvider(
     provider_name="vehicle_gear",
     elements=["Manual","Automatic"]
)

currency_list_provider = DynamicProvider(
     provider_name="vehicle_currency",
     elements=["Euro","USD"]
)

fake = Faker()
fake.add_provider(makers_list_provider)
fake.add_provider(model_type_provider)
fake.add_provider(fuel_type_provider)
fake.add_provider(gear_type_provider)
fake.add_provider(currency_list_provider)

def generate_vehicle_data(num_records=100):
    data_records = []
    for i in range(num_records):
        record = {
            "Vehicle ID": f"V{str(4000+i)}",
            "Country": fake.country(),
            "Make": fake.vehicle_makers(),
            "Model": fake.vehicle_model(),
            "Year": fake.random_int(min=2010, max=2025),
            "Mileage": str(fake.random_int(min=17, max=25))+"kmpl", #SUV & EV car mileage range should be different
            "Fuel": fake.vehicle_fuel(),
            "Gear Type": fake.vehicle_gear(),
            "Horsepower": fake.random_int(min=80, max=220), #SUV & EV car Horsepower range should be different
            "Price": fake.random_int(min=1000, max=5000),  #Price 
            "Currency": fake.vehicle_currency(),
            "Preowned": choice(["Yes","No"]),
            "Inserted Date": fake.date_between_dates(
                date_start=datetime(2022,1,1),
                date_end=datetime(2025,7,31)
            )
        }
        data_records.append(record)
    return pd.DataFrame(data_records)

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
                date_start=datetime(2022,1,1), 
                date_end=datetime(2025,8,1)
            )
        }
        data_records.append(record)
    return pd.DataFrame(data_records)

def generate_contract_data(num_records=100):
    # Pools
    existing_customer_pool = [fake.unique.random_int(min=1000, max=2000) for _ in range(100)]  # reused
    vehicle_ids = ["V"+str(4000+fake.unique.random_int(min=1, max=100)) for _ in range(100)]
    product_ids = ["P"+str(1000+fake.unique.random_int(min=1000, max=1050)) for _ in range(50)]

    used_new_customers = set()
    contracts = []
    data_records = []

    for i in range(1, num_records + 1):
        # Decide if existing or new customer
        if randint(1, 100) <= 60:  # 60% chance existing
            customer_id = choice(existing_customer_pool)
            existing_customer = "yes"
        else:
            # Ensure new customer appears only once
            while True:
                customer_id = fake.unique.random_int(min=2001, max=5000)
                if customer_id not in used_new_customers:
                    used_new_customers.add(customer_id)
                    break
            existing_customer = "no"

        # Discount and preferred flags
        discount_applied = "yes" if existing_customer == "yes" and randint(1, 100) <= 30 else "no"
        preferred_customer = "yes" if existing_customer == "yes" and randint(1, 100) <= 20 else "no"

        # Lease dates
        lease_start = fake.date_between(start_date="-2y", end_date="today")
        lease_term_months = choice([12, 24, 36, 48])
        lease_expiry = lease_start + timedelta(days=lease_term_months*30)

        # Other fields
        vehicle_id = choice(vehicle_ids)
        product_id = choice(product_ids)
        monthly_emi = randint(300, 1000)
        road_assistance = choice(["yes", "no"])
        maintenance = choice(["yes", "no"])

        # Contract dict
        contract = {
            "Contract ID": i,
            "Customer ID": customer_id,
            "Existing Customer": existing_customer,
            "Vehicle ID": vehicle_id,
            "Product ID": product_id,
            "Monthly EMI": monthly_emi,
            "Lease Start Date": lease_start,
            "Lease Expiry Date": lease_expiry,
            "Road Assistance": road_assistance,
            "Maintenance": maintenance,
            "Discount Applied": discount_applied,
            "Preferred Customer": preferred_customer
        }
        contracts.append(contract)

        # Contract summary for vector DB
        summary = (
            f"Contract {i}: Lease of Vehicle {vehicle_id} under Product {product_id} "
            f"with Lease Start Date: {lease_start}, Lease Expiry Date: {lease_expiry}, "            
            f"for {lease_term_months} months, EMI {monthly_emi} USD, "
            f"Road Assistance: {road_assistance}, Maintenance: {maintenance}, "
            f"Existing Customer: {existing_customer}, Discount Applied: {discount_applied}, "
            f"Preferred Customer: {preferred_customer}"
        )

        record = {
            "Summary": summary,
            "Contract ID": i,
            "Customer ID": customer_id,
            "Vehicle ID": vehicle_id,
            "Product ID": product_id,
        }
        data_records.append(record)        
        
    return pd.DataFrame(contracts), pd.DataFrame(data_records)

# --- Generate & Save ---
num_records = 100
#vehicle_data = generate_vehicle_data(num_records)
#vehicle_data.to_csv("vehicle_data.csv",index=False)
#print(vehicle_data.head())

num_records = 50
#leasing_data = generate_leasing_data(num_records)
#leasing_data.to_csv("leasing_data.csv", index=False)
#print(leasing_data.head())

num_records = 500
#df_contracts, customer_contract_data = generate_contract_data(num_records)
#df_contracts.to_csv("contract_data.csv", index=False)
#customer_contract_data.to_csv("customer_contract_data.csv", index=False)
#print(df_contracts.head())
#print(customer_contract_data.head())