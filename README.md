# Lease-Chat-Assistant

1. datasetgen.py <br> 
    Generates vehicle data using faker library and saves into vehicle_data.csv

2. vectordb populate.py <br> 
    Adds data from vehicle_data.csv to the weaviate db

3. vectordb search.py <br>
    Performs near_text search and hybrid search on the vector db 