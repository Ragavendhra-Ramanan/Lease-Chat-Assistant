import pandas as pd
from faker import Faker
from faker.providers import DynamicProvider
from datetime import datetime
from random import choice

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
            "Mileage": str(fake.random_int(min=17, max=25))+" kmpl", 
            "Fuel": fake.vehicle_fuel(),
            "Gear Type": fake.vehicle_gear(),
            "Horsepower": fake.random_int(min=80, max=220),
            "Price": fake.random_int(min=1000, max=5000),
            "Currency": fake.vehicle_currency(),
            "Preowned": choice(["Yes","No"]),
            "Inserted Date": fake.date_between_dates(
                date_start=datetime(2022,1,1),
                date_end=datetime(2025,7,31)
            )
        }
        data_records.append(record)
    
    df = pd.DataFrame(data_records)

    # Add concatenated text column
    df["Summary"] = df.apply(lambda row: (
        f"Country: {row['Country']}, Make: {row['Make']}, Model: {row['Model']}, Year: {row['Year']}, "
        f"Mileage: {row['Mileage']}, Fuel: {row['Fuel']}, Gear: {row['Gear Type']}, "
        f"Horsepower: {row['Horsepower']}, Price: {row['Price']} {row['Currency']}, "
        f"Preowned: {row['Preowned']}, Inserted: {row['Inserted Date']}"
    ), axis=1)

    return df, df[["Summary","Vehicle ID"]]



# --- Generate & Save ---
num_records = 100
if __name__ == "__main__":
    vehicle_data, vehicle_chunk_data = generate_vehicle_data(num_records)
    vehicle_data.to_csv("../data/vehicle_data.csv",index=False)
    vehicle_chunk_data.to_csv("../data/vehicle_chunk_data.csv",index=False)
    print(vehicle_data.head())

