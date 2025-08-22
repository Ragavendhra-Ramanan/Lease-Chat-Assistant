import pandas as pd
from faker import Faker
from faker.providers import DynamicProvider
from datetime import datetime

model_type_provider = DynamicProvider(
     provider_name="vehicle_model",
     elements=["Sedan","Hatchback","SUV"],
)

fuel_type_provider = DynamicProvider(
     provider_name="vehicle_fuel",
     elements=["Petrol","Diesel","EV"],
)

gear_type_provider = DynamicProvider(
     provider_name="vehicle_gear",
     elements=["Manual","Automatic"],
)

currency_list = ["Euro","USD"]
makers_list = ["Toyota", "Volkswagen", "Hyundai", "Honda", "Maruti Suzuki", "Tata Motors", "Mahindra"]

fake = Faker()
fake.add_provider(model_type_provider)
fake.add_provider(fuel_type_provider)
fake.add_provider(gear_type_provider)

def generate_vehicle_data(num_records=100):
    data_records = []
    for _ in range(num_records):
        record = {
            "Vehicle ID": fake.unique.random_int(min=1,max=100),
            "Country": fake.country(),
            "Make": fake.random_element(makers_list),
            "Model": fake.vehicle_model(),
            "Year": fake.random_int(min=2010, max=2025),
            "Mileage": str(fake.random_int(min=17, max=25))+"kmpl", #SUV & EV car mileage range should be different
            "Fuel": fake.vehicle_fuel(),
            "Gear Type": fake.vehicle_gear(),
            "Horsepower": fake.random_int(min=80, max=220), #SUV & EV car Horsepower range should be different
            "Price": fake.random_int(min=1000, max=5000),  #Price 
            "Currency": fake.random_element(currency_list),
            "Preowned": fake.boolean(),
            "Inserted date": fake.date_between_dates(date_start=datetime(2022,1,1),date_end=datetime(2025,7,31))
        }
        data_records.append(record)
    return pd.DataFrame(data_records)

vehicle_data = generate_vehicle_data(100)
vehicle_data.to_csv("vehicle_data.csv",index=False)
print(vehicle_data.head())