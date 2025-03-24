import pandas as pd
import folium
import re
from jinja2 import Template
from matplotlib import colormaps
from matplotlib.colors import to_hex

# Load the CSV data
df = pd.read_csv('../California-Broadband-Visuals-Stats/data/California_Broadband_Summary.csv')

# Define coverage columns
coverage_cols_4g = ['mobilebb_4g_area_st_pct']
coverage_cols_5g = ['mobilebb_5g_spd1_area_st_pct', 'mobilebb_5g_spd2_area_st_pct']

df['min_4g_coverage'] = df[coverage_cols_4g].min(axis=1, skipna=True)
df['min_5g_coverage'] = df[coverage_cols_5g].min(axis=1, skipna=True)

# Parse geocode.txt into a DataFrame
geocode_data = []
with open('../California-Broadband-Visuals-Stats/data/geocode.txt', 'r') as file:
    for line in file:
        match = re.match(r"Geocoded (.+?): (-?\d+\.\d+), (-?\d+\.\d+)", line.strip())
        if match:
            place_name, latitude, longitude = match.groups()
            place_name = place_name.replace(" (simplified)", "").strip()
            geocode_data.append([place_name, float(latitude), float(longitude)])

geocode_df = pd.DataFrame(geocode_data, columns=['geography_desc', 'latitude', 'longitude'])

# Merge geocoded data with full dataset
merged_df = df.merge(geocode_df, on='geography_desc', how='inner')

# Drop rows with missing or invalid coordinates
merged_df = merged_df.dropna(subset=['latitude', 'longitude'])

# Filter coordinates to California bounds
merged_df = merged_df[
    (merged_df['latitude'].between(32, 42)) &
    (merged_df['longitude'].between(-124, -114))
]

print(f"Total places mapped: {len(merged_df)}")

def get_color(coverage_pct, colormap_name):
    colormap = colormaps[colormap_name]
    normalized = max(0, min(1 - coverage_pct, 1))
    return to_hex(colormap(normalized))

# Create maps
map_4g = folium.Map(location=[36.7783, -119.4179], zoom_start=6)
map_5g = folium.Map(location=[36.7783, -119.4179], zoom_start=6)

# Prepare sorted lists
sorted_4g = merged_df[['geography_desc', 'min_4g_coverage']].sort_values('min_4g_coverage')
sorted_5g = merged_df[['geography_desc', 'min_5g_coverage']].sort_values('min_5g_coverage')

# Generate list HTML
list_4g_html = '<ul>' + ''.join(
    f'<li>{row["geography_desc"]}: {row["min_4g_coverage"]*100:.1f}%</li>'
    for _, row in sorted_4g.iterrows()
) + '</ul>'

list_5g_html = '<ul>' + ''.join(
    f'<li>{row["geography_desc"]}: {row["min_5g_coverage"]*100:.1f}%</li>'
    for _, row in sorted_5g.iterrows()
) + '</ul>'

for _, row in merged_df.iterrows():
    coverage_4g = row['min_4g_coverage'] * 100
    coverage_5g = row['min_5g_coverage'] * 100
    color_4g = get_color(row['min_4g_coverage'], 'YlOrRd')
    color_5g = get_color(row['min_5g_coverage'], 'YlOrRd')
    popup_text_4g = f"{row['geography_desc']}<br>4G Min Coverage: {coverage_4g:.1f}%"
    popup_text_5g = f"{row['geography_desc']}<br>5G Min Coverage: {coverage_5g:.1f}%"

    marker_4g = folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        popup=popup_text_4g,
        color=color_4g,
        fill=True,
        fill_color=color_4g,
        fill_opacity=0.7,
        tooltip=popup_text_4g
    )
    
    marker_5g = folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        popup=popup_text_5g,
        color=color_5g,
        fill=True,
        fill_color=color_5g,
        fill_opacity=0.7,
        tooltip=popup_text_5g
    )

    marker_4g.add_to(map_4g)
    marker_5g.add_to(map_5g)

# Save individual maps as HTML strings
map_4g_html = map_4g.get_root().render()
map_5g_html = map_5g.get_root().render()

# Create the combined HTML file with maps and lists
html_content = Template(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4G & 5G Coverage Map</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            display: flex;
            width: 100%;
            height: 60vh;
        }}
        .map-container {{
            width: 50%;
            height: 100%;
            position: relative;
        }}
        #map_4g, #map_5g {{
            width: 100%;
            height: 100%;
        }}
        .map-label {{
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.8);
            padding: 5px 10px;
            border-radius: 3px;
            z-index: 1000;
            font-size: 16px;
            font-weight: bold;
        }}
        .list-container {{
            display: flex;
            width: 100%;
            height: 40vh;
            overflow: auto;
        }}
        .list-section {{
            width: 50%;
            padding: 10px;
            box-sizing: border-box;
        }}
        .list-section h2 {{
            margin-top: 0;
            text-align: center;
        }}
        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        li {{
            padding: 2px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="map-container">
            <div class="map-label">4G Coverage</div>
            <div id="map_4g">{map_4g_html}</div>
        </div>
        <div class="map-container">
            <div class="map-label">5G Coverage</div>
            <div id="map_5g">{map_5g_html}</div>
        </div>
    </div>
    <div class="list-container">
        <div class="list-section">
            <h2>4G Coverage (Lowest to Highest)</h2>
            {list_4g_html}
        </div>
        <div class="list-section">
            <h2>5G Coverage (Lowest to Highest)</h2>
            {list_5g_html}
        </div>
    </div>
</body>
</html>
""")

# Save the final combined map
with open("../California-Broadband-Visuals-Stats/html/combined_coverage_map.html", "w") as file:
    file.write(html_content.render())

print("Combined map with coverage lists saved as 'combined_coverage_map.html'.")