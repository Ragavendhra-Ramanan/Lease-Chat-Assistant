import pandas as pd
from faker import Faker
from datetime import datetime
from random import choice
from faker.providers import DynamicProvider

import random
import pandas as pd
from faker import Faker
from datetime import datetime

fake = Faker()

# Fixed realistic product templates
product_templates = [
    {
        "name": "Standard Lease",
        "desc": "A predictable monthly payment plan for everyday drivers with full maintenance included.",
        "tax_saving": "No",
        "flexi_allowed": False
    },
    {
        "name": "Dynamic Lease",
        "desc": "Flexible lease with upgrade or exit options after mid-term, ideal for dynamic users.",
        "tax_saving": "No",
        "flexi_allowed": True
    },
    {
        "name": "Value Lease",
        "desc": "Affordable leasing for small cars with lower monthly costs and basic maintenance.",
        "tax_saving": "No",
        "flexi_allowed": False
    },
    {
        "name": "Corporate Saver",
        "desc": "Business-focused lease offering tax deductions, bundled insurance, and priority servicing.",
        "tax_saving": "Yes",
        "flexi_allowed": False
    },
    {
        "name": "Eco Mobility",
        "desc": "Green lease plan for EVs and hybrids, including charging and maintenance support.",
        "tax_saving": "Yes",
        "flexi_allowed": True
    },
    {
        "name": "Premium EV Lease",
        "desc": "Exclusive EV lease with charging benefits, subsidies, and zero-emission perks.",
        "tax_saving": "Yes",
        "flexi_allowed": True
    },    
    {
        "name": "FamilyRide Lease",
        "desc": "Designed for family cars with long-term stability, garage maintenance, and roadside cover.",
        "tax_saving": "No",
        "flexi_allowed": False
    }   
]

lease_terms = [12, 24, 36, 48]
renewal_cycles = ["Quarterly", "Bi-Annual", "Annual"]

def generate_product(pid):
    tpl = random.choice(product_templates)
    lease_term = random.choice(lease_terms)

    # Flexi logic
    flexi_lease = "Yes" if tpl["flexi_allowed"] and lease_term <= 24 else "No"

    # Renewal logic
    if lease_term <= 12:
        renewal_cycle = "Quarterly"
    elif lease_term == 24:
        renewal_cycle = random.choice(["Bi-Annual", "Annual"])
    else:
        renewal_cycle = "Annual"

    # Maintenance logic
    maintenance_type = "Roadside" if flexi_lease == "Yes" else "Garage"

    # Insert realistic date (last 18 months)
    inserted_date = fake.date_between(start_date="-18M", end_date="today")

    # Build description
    desc = f"{tpl['desc']} Lease term is {lease_term} months, renewal is {renewal_cycle.lower()}."

    # Build summary
    summary = f"{tpl['name']}, {lease_term} months, Flexi: {flexi_lease}, Tax Saving: {tpl['tax_saving']}, Renewal: {renewal_cycle}, Maintenance: {maintenance_type}"

    return {
        "Product ID": f"P{1000+pid}",
        "Product Name": tpl["name"],
        "Short Description": desc,
        "Lease Term": lease_term,
        "Flexi Lease": flexi_lease,
        "Tax Saving Plan": tpl["tax_saving"],
        "Renewal Cycle": renewal_cycle,
        "Maintenance Type": maintenance_type,
        "Inserted Date": inserted_date,
        "Summary": summary
    }

# Generate 20 realistic products
num_records=20
products = [generate_product(i) for i in range(num_records)]
df = pd.DataFrame(products)
leasing_chunk_data = df[["Summary","Product ID"]]

# Save as CSV
df.to_csv("../data/leasing_data_new.csv", index=False)
leasing_chunk_data.to_csv("../data/leasing_chunk_data_new.csv",index=False)


print(df.head(10))

"""
1. Product Templates (Real Business Archetypes)
Instead of letting Faker invent nonsense, I predefined 10 realistic product types:
Standard Lease → predictable monthly, stable
Flexi Lease → exit/upgrade early
Corporate Saver / Business Advantage → tax-deduction plans for companies
Premium EV Lease / Eco Mobility → EV- and hybrid-specific with charging perks
Luxury Drive → concierge, garage-based maintenance for premium cars
Family Plan / Compact Saver → practical, cheaper, stable options
Each template comes with:
name
description (brochure-style)
whether it allows flexi
whether it’s tax_saving
This makes sure product names/descriptions are consistent and believable.
2. Lease Term Logic
Lease terms chosen from 12, 24, 36, 48 months (real-world standard durations).
Flexi plans usually available only for shorter terms (≤ 24 months).
Long leases (36–48 months) = stable, not flexi.
3. Renewal Cycle Logic
If 12 months → renewal cycle is Quarterly (frequent checks).
If 24 months → can be Bi-Annual or Annual.
If 36–48 months → always Annual renewal (too long for frequent renewals).
4. Flexi Lease Logic
If the template allows flexi and lease term ≤ 24 months → Flexi = Yes.
Otherwise → Flexi = No.
This mimics real-world where flexibility is offered only on short/medium leases.
5. Maintenance Type Logic
If Flexi Lease = Yes → Maintenance = Roadside (since cars change more, easier roadside support).
If Flexi Lease = No → Maintenance = Garage (stable cars, scheduled servicing).
6. Tax Saving Plan Logic
Corporate / EV products → Always Yes (since these are deductible or government-incentivized).
Luxury / Family / Compact plans → No (personal usage, not deductible).
7. Inserted Date
Generated within last 18 months (to simulate new product launches gradually entering the catalog).
8. Short Description
Starts with the template brochure text,
Then appends lease term and renewal cycle info,
e.g.
“Exclusive EV lease with charging benefits. Lease term is 24 months, renewal is annual.”
This makes descriptions read like sales collateral.
9. Summary
Compact string with key fields:
"Premium EV Lease, 24 months, Flexi: Yes, Tax Saving: Yes, Renewal: Annual, Maintenance: Roadside"
Useful for quick filtering or search indexing.
"""
