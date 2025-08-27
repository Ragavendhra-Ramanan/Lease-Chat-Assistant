import random
import pandas as pd
from faker import Faker
from datetime import datetime

fake = Faker()

# Some car makes and models for realism (includes EVs)
car_data = {
    "Tesla": ["Model S", "Model 3", "Model X", "Model Y"],
    "Toyota": ["Corolla", "Camry", "Prius", "RAV4"],
    "Honda": ["Civic", "Accord", "CR-V", "Fit"],
    "BMW": ["3 Series", "5 Series", "X3", "i3 (EV)"],
    "Audi": ["A3", "A4", "Q5", "e-tron (EV)"],
    "Ford": ["Focus", "Fusion", "Mustang", "F-150 Lightning (EV)"],
    "Hyundai": ["Elantra", "Sonata", "Kona", "Ioniq 5 (EV)"],
    "Nissan": ["Altima", "Maxima", "Leaf (EV)", "Rogue"],
    "Volkswagen": ["Golf", "Passat", "ID.4 (EV)", "Tiguan"],
}

fuel_types = ["Petrol", "Diesel", "Hybrid", "EV"]
gear_types = ["Manual", "Automatic"]
currencies = ["USD", "EUR", "INR", "GBP"]

def generate_car_dataset(n=20):
    records = []

    for i in range(n):
        make = random.choice(list(car_data.keys()))
        model = random.choice(car_data[make])

        # EV check: if model contains EV keywords, fuel = EV
        if "EV" in model or "e-tron" in model or "Lightning" in model or "i3" in model or "Ioniq" in model or "Leaf" in model or "ID.4" in model:
            fuel = "EV"
        else:
            fuel = random.choice(fuel_types)

        year = random.randint(2005, 2024)
        mileage = round(random.uniform(5, 25), 1) if fuel != "EV" else round(random.uniform(3, 8), 1)  # kmpl or efficiency scale
        horsepower = random.randint(80, 450) if fuel != "EV" else random.randint(120, 600)
        price = random.randint(4000, 80000)
        currency = random.choice(currencies)
        preowned = random.choice(["Yes", "No"])
        inserted_date = fake.date_between(start_date="-2y", end_date="today")
        country = fake.country()
        gear = random.choice(gear_types)

        vehicle_id = f"V{1000+i}"

        summary = (f"Country: {country}, Make: {make}, Model: {model}, Year: {year}, "
                   f"Mileage: {mileage} kmpl, Fuel: {fuel}, Gear: {gear}, "
                   f"Horsepower: {horsepower}, Price: {price} {currency}, "
                   f"Preowned: {preowned}")

        records.append({
            "Vehicle ID": vehicle_id,
            "Country": country,
            "Make": make,
            "Model": model,
            "Year": year,
            "Mileage": mileage,
            "Fuel": fuel,
            "Gear Type": gear,
            "Horsepower": horsepower,
            "Price": price,
            "Currency": currency,
            "Preowned": preowned,
            "Inserted Date": inserted_date,
            "Summary": summary
        })

    df = pd.DataFrame(records)
    return df, df[["Summary","Vehicle ID"]]



# --- Generate & Save ---
num_records = 100
if __name__ == "__main__":
    vehicle_data, vehicle_chunk_data = generate_car_dataset(num_records)
    vehicle_data.to_csv("../data/vehicle_data.csv",index=False)
    vehicle_chunk_data.to_csv("../data/vehicle_chunk_data.csv",index=False)
    print(vehicle_data.head())

