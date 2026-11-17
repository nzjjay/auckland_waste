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

# Labels for the date-keyed attribute (e.g. "2026-09-10": "Food scraps").
# These match the bin names used by third-party cards such as wheelie-bin-card.
WASTE_TYPE_COLLECTION_LABELS = {
    WASTE_TYPE_RUBBISH: "Rubbish",
    WASTE_TYPE_RECYCLE: "Recycling",
    WASTE_TYPE_FOOD_WASTE: "Food scraps",
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
# The council site's WAF checks both Accept and User-Agent headers.
# This Firefox User-Agent resolves the HTTP 406 responses reported in #10.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:159.0) Gecko/20100101 Firefox/159.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
