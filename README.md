# Auckland Waste Collection

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration for Auckland Waste Collection that fetches rubbish, recycling, and food waste collection days from Auckland Council.

## Features

- 🗑️ **Rubbish** collection day sensor
- ♻️ **Recycling** collection day sensor
- 🍎 **Food Waste** collection day sensor
- 📅 Shows days until next collection
- 🎨 Custom Lovelace card for beautiful display
- 🔄 Automatic updates every 12 hours

## Screenshot

<img src="images/card-example.png" alt="Waste Collection Card" width="400">

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL with category "Integration"
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/auckland_waste` folder to your Home Assistant's `custom_components` directory
2. Copy `www/auckland-waste-card.js` to your Home Assistant's `www` folder
3. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Auckland Waste Collection"
4. Enter your area number

### Finding Your Area Number (Assessment Number)

1. Go to [Auckland Council's collection day finder](https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days.html)
2. Enter your address and search
3. The **assessment number** shown for your property is your area number (e.g., `12345678901`)

## Sensors

The integration creates three sensors for each configured area:

| Sensor | Description |
|--------|-------------|
| `sensor.auckland_waste_XXX_rubbish` | Next rubbish collection date |
| `sensor.auckland_waste_XXX_recycling` | Next recycling collection date |
| `sensor.auckland_waste_XXX_food_waste` | Next food waste collection date |

### Sensor Attributes

Each sensor includes the following attributes:

- `date` - Collection date (YYYY-MM-DD)
- `day_of_week` - Day of the week (e.g., "Wednesday")
- `formatted_date` - Human-readable date (e.g., "Wednesday, 8 October")
- `days_until` - Number of days until collection
- `is_today` - True if collection is today
- `is_tomorrow` - True if collection is tomorrow
- `waste_type` - Type of waste (rubbish, recycle, food-waste)
- `area_number` - Your Auckland Council area number

## Custom Card

### Adding the Card Resource

Add the following to your Lovelace resources:

1. Go to **Settings** → **Dashboards** → **Resources** (three dots menu)
2. Click **+ Add Resource**
3. Enter `/local/auckland-waste-card.js`
4. Select "JavaScript Module"
5. Click "Create"

### Using the Card

Add the card to your dashboard:

```yaml
type: custom:auckland-waste-card
title: Waste Collection
entities:
  - sensor.auckland_waste_702_rubbish
  - sensor.auckland_waste_702_recycling
  - sensor.auckland_waste_702_food_waste
```

Or use the area number directly:

```yaml
type: custom:auckland-waste-card
title: Waste Collection
area_number: "702"
```

## Example Automations

### Notification the Day Before Collection

```yaml
automation:
  - alias: "Rubbish Day Reminder"
    trigger:
      - platform: state
        entity_id: sensor.auckland_waste_702_rubbish
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.auckland_waste_702_rubbish', 'is_tomorrow') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🗑️ Rubbish Day Tomorrow"
          message: "Put out the rubbish bin tonight!"
```

### Morning Reminder on Collection Day

```yaml
automation:
  - alias: "Collection Day Morning Reminder"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: or
        conditions:
          - condition: template
            value_template: "{{ state_attr('sensor.auckland_waste_702_rubbish', 'is_today') }}"
          - condition: template
            value_template: "{{ state_attr('sensor.auckland_waste_702_recycling', 'is_today') }}"
          - condition: template
            value_template: "{{ state_attr('sensor.auckland_waste_702_food_waste', 'is_today') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "♻️ Waste Collection Today"
          message: >
            Today's collections:
            {% if state_attr('sensor.auckland_waste_702_rubbish', 'is_today') %}🗑️ Rubbish {% endif %}
            {% if state_attr('sensor.auckland_waste_702_recycling', 'is_today') %}♻️ Recycling {% endif %}
            {% if state_attr('sensor.auckland_waste_702_food_waste', 'is_today') %}🍎 Food Waste {% endif %}
```

## Troubleshooting

### Integration Not Finding Data

- Verify your area number is correct
- Check if the Auckland Council website is accessible
- Look at Home Assistant logs for error messages

### Card Not Showing

- Make sure you've added the card resource
- Clear your browser cache
- Check the browser console for JavaScript errors

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This integration is not affiliated with or endorsed by Auckland Council. It scrapes publicly available data from the Auckland Council website.
