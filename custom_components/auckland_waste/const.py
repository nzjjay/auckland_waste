"""Constants for Auckland Waste Collection integration."""

DOMAIN = "auckland_waste"

CONF_AREA_NUMBER = "area_number"

# Waste types
WASTE_TYPE_RUBBISH = "rubbish"
WASTE_TYPE_RECYCLE = "recycle"
WASTE_TYPE_FOOD_WASTE = "food-waste"

# Friendly names for waste types
WASTE_TYPE_NAMES = {
    WASTE_TYPE_RUBBISH: "Rubbish",
    WASTE_TYPE_RECYCLE: "Recycling",
    WASTE_TYPE_FOOD_WASTE: "Food Waste",
}

# Icons for waste types
WASTE_TYPE_ICONS = {
    WASTE_TYPE_RUBBISH: "mdi:trash-can",
    WASTE_TYPE_RECYCLE: "mdi:recycle",
    WASTE_TYPE_FOOD_WASTE: "mdi:food-apple",
}

# Update interval (once per day)
UPDATE_INTERVAL_HOURS = 12

# API URL
API_URL = "https://new.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{area_number}.html"

# Request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
