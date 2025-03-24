import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
import os
import random

def geocode_csv(input_csv_path, output_txt_path):
    """
    Geocode locations from a CSV file and save the coordinates to a text file.
    
    Args:
        input_csv_path: Path to the input CSV file
        output_txt_path: Path to the output text file
    """
    # Read the CSV file
    df = pd.read_csv(input_csv_path)
    
    # Initialize geocoder with longer timeout
    geolocator = Nominatim(user_agent="california_broadband_geocoder", timeout=10)
    
    # Create or open the output file
    with open(output_txt_path, 'w') as f:
        # Process each row in the dataframe
        for idx, row in df.iterrows():
            # Extract location name from the geography_desc column
            location_raw = row['geography_desc']
            
            # Clean up the location string for geocoding (remove CDP and CA references)
            location = location_raw.replace(" CDP", "").replace(", CA", "")
            
            # Create a clean version of the raw location for output display 
            # (remove CDP but keep the CA part)
            display_location = location_raw.replace(" CDP", "")
            
            # Print progress
            print(f"Geocoding {idx+1}/{len(df)}: {location}")
            
            # Try to geocode the location with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Add random delay between 1-3 seconds to avoid rate limiting
                    delay = 1 + random.random() * 2
                    time.sleep(delay)
                    
                    # Geocode location
                    geo_result = geolocator.geocode(location)
                    
                    if geo_result:
                        # Write the result to the file in the specified format
                        f.write(f"Geocoded {display_location}: {geo_result.latitude}, {geo_result.longitude}\n")
                        print(f"  Found: {geo_result.latitude}, {geo_result.longitude}")
                        break
                    elif attempt == max_retries - 1:  # Last attempt
                        # Try with 'California' added
                        time.sleep(delay)
                        geo_result = geolocator.geocode(f"{location}, California")
                        
                        if geo_result:
                            f.write(f"Geocoded {location}, CA (simplified): {geo_result.latitude}, {geo_result.longitude}\n")
                            print(f"  Found with California added: {geo_result.latitude}, {geo_result.longitude}")
                        else:
                            # If it still fails, write coordinates as N/A
                            f.write(f"Could not geocode {display_location}: N/A, N/A\n")
                            print("  Not found")
                
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    print(f"  Attempt {attempt+1}/{max_retries} failed: {e}")
                    if attempt == max_retries - 1:  # If this was the last attempt
                        f.write(f"Error geocoding {display_location}: N/A, N/A\n")
                        print(f"  All {max_retries} attempts failed for {location}")
                    else:
                        # Wait longer before retrying
                        time.sleep(3 + random.random() * 2)

if __name__ == "__main__":
    # Define file paths
    input_file = "../California-Broadband-Visuals-Stats/data/California_Broadband_Summary.csv"
    output_file = "../California-Broadband-Visuals-Stats/data/full_geocode.txt"
    
    # Run the geocoding function for all entries
    geocode_csv(input_file, output_file)
    
    print(f"\nGeocoding complete. Results saved to {output_file}")