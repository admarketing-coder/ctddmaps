from flask import Flask, request, jsonify, render_template
import pandas as pd
import re
import random
import requests

app = Flask(__name__)

MAPBOX_ACCESS_TOKEN = 'pk.eyJ1IjoiemVudHJhZGVzLW9uYm9hcmRpbmciLCJhIjoiY2x6dHdpbG9yMGdxejJtczV5eHZyajU5cSJ9.css9wXCRUwiSAm0tuCmM_Q'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_csv', methods=['POST'])
def process_csv():
    file = request.files['file']
    if not file:
        return jsonify({'error': 'No file uploaded'}), 400

    df = pd.read_csv(file)
    locations = []
    job_type_colors = {}

    def generate_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    for _, row in df.iterrows():
        address = row['Service Address']
        job_type = row['Job Type']

        # Assign a color to the job type if it doesn't already have one
        if job_type not in job_type_colors:
            job_type_colors[job_type] = generate_color()

        color = job_type_colors[job_type]

        # Use Mapbox Geocoding API to get the latitude and longitude
        geocode_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{address}.json?access_token={MAPBOX_ACCESS_TOKEN}"
        response = requests.get(geocode_url)
        if response.status_code == 200:
            data = response.json()
            if data['features']:
                location = data['features'][0]
                ticket_number = re.sub(r'[^a-zA-Z0-9]', '', str(row['Ticket Number']))
                locations.append({
                    'ticket_number': ticket_number,
                    'customer': str(row['Customer Name']),
                    'address': address,
                    'latitude': location['geometry']['coordinates'][1],  # latitude
                    'longitude': location['geometry']['coordinates'][0],  # longitude
                    'color': color,
                    'description': str(row['Job Description']),
                    'technician': str(row['Technician(s)'])
                })
            else:
                print(f"Geocoding failed for address: {address}")
        else:
            print(f"Geocoding request failed with status code {response.status_code}")

    return jsonify({'locations': locations, 'job_type_colors': job_type_colors})

if __name__ == '__main__':
    app.run(debug=True)
