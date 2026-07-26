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
API_URL = "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{area_number}.html"

# Request headers
# The council site's WAF returns HTTP 406 (Not Acceptable) when either:
#   - no Accept header is sent, or
#   - the User-Agent claims an outdated browser (Chrome <= 120 is blocked).
# Keep the User-Agent reasonably current if 406 errors reappear.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
