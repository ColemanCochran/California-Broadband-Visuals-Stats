import pandas as pd
import folium
import re
from jinja2 import Template
from matplotlib import colormaps
from matplotlib.colors import to_hex
import os

# Paths for PNG files
png_paths = [
    '/files/spacex_project/png/avg_broadband_by_type.png',
    '/files/spacex_project/png/broadband_percent_instances.png',
    '/files/spacex_project/png/coverage_by_area.png',
    '/files/spacex_project/png/rural_coverage.png'
]

# Output path for the final HTML
html_output_path = '/files/spacex_project/html/california_coverage.html'

# --- Map Generation Logic ---

# Load the CSV data
df = pd.read_csv('/files/spacex_project/data/California_Broadband_Summary.csv')

# Define coverage columns
coverage_cols_4g = ['mobilebb_4g_area_st_pct']
coverage_cols_5g = ['mobilebb_5g_spd1_area_st_pct', 'mobilebb_5g_spd2_area_st_pct']

df['min_4g_coverage'] = df[coverage_cols_4g].min(axis=1, skipna=True)
df['min_5g_coverage'] = df[coverage_cols_5g].min(axis=1, skipna=True)

# Parse geocode.txt into a DataFrame
geocode_data = []
with open('/files/spacex_project/data/geocode.txt', 'r') as file:
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

# Prepare sorted lists and store coordinates
sorted_4g = merged_df[['geography_desc', 'min_4g_coverage', 'latitude', 'longitude']].sort_values('min_4g_coverage')
sorted_5g = merged_df[['geography_desc', 'min_5g_coverage', 'latitude', 'longitude']].sort_values('min_5g_coverage')

# Generate list HTML with onclick events
list_4g_html = '<ul>' + ''.join(
    f'<li onclick="zoomToLocation(\'map_4g\', {row["latitude"]}, {row["longitude"]})">{row["geography_desc"]}: {row["min_4g_coverage"]*100:.1f}%</li>'
    for _, row in sorted_4g.iterrows()
) + '</ul>'

list_5g_html = '<ul>' + ''.join(
    f'<li onclick="zoomToLocation(\'map_5g\', {row["latitude"]}, {row["longitude"]})">{row["geography_desc"]}: {row["min_5g_coverage"]*100:.1f}%</li>'
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

# --- Embed PNG Images into the HTML ---

# Create HTML for the graph section
graph_html = """
<div class="graph-container">
    <h2>Coverage Distribution Graphs</h2>
    <div class="graph-grid">
"""

# Add each PNG image to the graph section
for png_path in png_paths:
    # Extract the file name for the alt text
    png_name = os.path.basename(png_path).replace('.png', '').replace('_', ' ').title()
    graph_html += f"""
        <div class="graph-item">
            <h3>{png_name}</h3>
            <img src="{png_path}" alt="{png_name}">
        </div>
    """

graph_html += """
    </div>
</div>
"""

# Create the combined HTML with maps, lists, and graphs
html_content = Template(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>California Broadband Coverage Map with Distribution Graphs</title>
    <style>
        body {{
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }}
        h1 {{
            font-size: 24px;
            margin: 20px 0;
            color: #333;
        }}
        .container {{
            display: flex;
            width: 90%;
            max-width: 1400px;
            height: 50vh;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .map-container {{
            width: 50%;
            height: 100%;
            position: relative;
            border: 1px solid #ddd;
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
            background: rgba(255, 255, 255, 0.9);
            padding: 8px 15px;
            border-radius: 5px;
            z-index: 1000;
            font-size: 16px;
            font-weight: bold;
            color: #333;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }}
        .list-container {{
            display: flex;
            width: 90%;
            max-width: 1400px;
            height: 20vh;
            margin-bottom: 30px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .list-section {{
            width: 50%;
            padding: 15px;
            box-sizing: border-box;
            overflow-y: auto;
        }}
        .list-section h2 {{
            margin: 0 0 10px 0;
            font-size: 18px;
            text-align: center;
            color: #444;
        }}
        ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        li {{
            padding: 5px 0;
            cursor: pointer;
            font-size: 14px;
            color: #555;
            border-bottom: 1px solid #eee;
        }}
        li:hover {{
            background-color: #f0f0f0;
            color: #000;
        }}
        .graph-container {{
            width: 90%;
            max-width: 1400px;
            margin: 0 auto 40px auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .graph-container h2 {{
            font-size: 20px;
            margin: 0 0 20px 0;
            text-align: center;
            color: #333;
        }}
        .graph-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 10px;
        }}
        .graph-item {{
            text-align: center;
        }}
        .graph-item h3 {{
            margin: 10px 0;
            font-size: 16px;
            color: #444;
        }}
        .graph-item img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
    </style>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body>
    <h1>California Broadband Coverage Analysis</h1>
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
    {graph_html}

    <script>
        let map4g, map5g;
        document.addEventListener('DOMContentLoaded', function() {{
            map4g = L.map('map_4g').setView([36.7783, -119.4179], 6);
            map5g = L.map('map_5g').setView([36.7783, -119.4179], 6);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: 'Map data © <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
            }}).addTo(map4g);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: 'Map data © <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
            }}).addTo(map5g);
            const parser = new DOMParser();
            const doc4g = parser.parseFromString(`{map_4g_html}`, 'text/html');
            const doc5g = parser.parseFromString(`{map_5g_html}`, 'text/html');
            const scripts4g = doc4g.getElementsByTagName('script');
            const scripts5g = doc5g.getElementsByTagName('script');
            for (let script of scripts4g) {{
                if (script.textContent.includes('addTo')) {{
                    eval(script.textContent);
                }}
            }}
            for (let script of scripts5g) {{
                if (script.textContent.includes('addTo')) {{
                    eval(script.textContent);
                }}
            }}
        }});

        function zoomToLocation(mapId, lat, lng) {{
            const zoomLevel = 10;
            if (mapId === 'map_4g' && map4g) {{
                map4g.setView([lat, lng], zoomLevel);
            }} else if (mapId === 'map_5g' && map5g) {{
                map5g.setView([lat, lng], zoomLevel);
            }}
        }}
    </script>
</body>
</html>
""")

# Save the final combined HTML
with open(html_output_path, 'w') as file:
    file.write(html_content.render())

print(f"Combined HTML with graphs saved as '{html_output_path}'")