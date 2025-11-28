# Auckland Waste Collection - Home Assistant Integration

## Project Overview
This is a Home Assistant custom integration for Auckland Waste Collection that fetches rubbish, recycling, and food waste collection days from Auckland Council.

## Project Structure
```
custom_components/
  auckland_waste/
    __init__.py          # Integration setup
    manifest.json        # Integration manifest (HACS compatible)
    config_flow.py       # UI configuration flow
    coordinator.py       # Data update coordinator
    sensor.py            # Sensor entities
    const.py             # Constants
    strings.json         # UI strings
    translations/        # Translations
      en.json
www/
  auckland-waste-card.js # Custom Lovelace card
```

## Development Guidelines
- Follow Home Assistant integration best practices
- Use DataUpdateCoordinator for data fetching
- Support HACS installation
- Implement config flow for UI-based setup
- Create sensor entities for each waste type (rubbish, recycling, food waste)

## Data Source
Auckland Council waste collection data is fetched from:
`https://new.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days/{area_number}.html`

## Installation
1. Copy `custom_components/auckland_waste` to your Home Assistant config directory
2. Copy `www/auckland-waste-card.js` to your www folder
3. Restart Home Assistant
4. Add integration via Settings > Devices & Services
