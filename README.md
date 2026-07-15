# AQI-Detector

## Clone the repo

git clone [https://github.com/PraneethUpadhya195/AQI-Detector](https://github.com/PraneethUpadhya195/AQI-Detector)<br>
cd your-repo-name

## Install requirements

pip install -r requirements.txt

## Setup .env

- Create a mongodb atlas cluster.
- Add this : MONGO_URI = "mongodb+srv://username:password@cluster-url/db-name?appName=clusterName"
- Create Open Weather Map API Key
- Add this : OWM_API_KEY = "API Key"

## Steps to run

1. python -m backend.app
2. python -m frontend.dashboard
