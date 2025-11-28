/**
 * Auckland Waste Collection Card
 * A custom Lovelace card for displaying Auckland waste collection days
 */

class AucklandWasteCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.entities && !config.area_number) {
      throw new Error('Please define entities or area_number');
    }
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 3;
  }

  static getConfigElement() {
    return document.createElement('auckland-waste-card-editor');
  }

  static getStubConfig() {
    return {
      title: 'Waste Collection',
      entities: []
    };
  }

  render() {
    if (!this._hass || !this.config) return;

    const entities = this.config.entities || this._getEntitiesByAreaNumber();
    
    const wasteData = entities.map(entityId => {
      const state = this._hass.states[entityId];
      if (!state) return null;
      
      return {
        entityId,
        name: state.attributes.friendly_name || entityId,
        date: state.state,
        daysUntil: state.attributes.days_until,
        dayOfWeek: state.attributes.day_of_week,
        formattedDate: state.attributes.formatted_date,
        wasteType: state.attributes.waste_type,
        isToday: state.attributes.is_today,
        isTomorrow: state.attributes.is_tomorrow
      };
    }).filter(Boolean);

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          padding: 16px;
        }
        .card-header {
          font-size: 1.5em;
          font-weight: 500;
          padding-bottom: 12px;
          color: var(--primary-text-color);
        }
        .waste-item {
          display: flex;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid var(--divider-color);
        }
        .waste-item:last-child {
          border-bottom: none;
        }
        .waste-icon {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 16px;
          font-size: 24px;
        }
        .waste-icon.rubbish {
          background-color: #ef5350;
          color: white;
        }
        .waste-icon.recycle {
          background-color: #66bb6a;
          color: white;
        }
        .waste-icon.food-waste {
          background-color: #ffa726;
          color: white;
        }
        .waste-info {
          flex: 1;
        }
        .waste-name {
          font-weight: 500;
          color: var(--primary-text-color);
        }
        .waste-date {
          color: var(--secondary-text-color);
          font-size: 0.9em;
        }
        .days-until {
          text-align: right;
          min-width: 80px;
        }
        .days-number {
          font-size: 1.5em;
          font-weight: bold;
          color: var(--primary-text-color);
        }
        .days-label {
          font-size: 0.8em;
          color: var(--secondary-text-color);
        }
        .today {
          color: #ef5350 !important;
        }
        .tomorrow {
          color: #ffa726 !important;
        }
        .no-data {
          color: var(--secondary-text-color);
          font-style: italic;
          padding: 16px 0;
        }
      </style>
      <ha-card>
        <div class="card-header">${this.config.title || 'Waste Collection'}</div>
        ${wasteData.length === 0 ? 
          '<div class="no-data">No waste collection data available</div>' :
          wasteData.map(item => this._renderWasteItem(item)).join('')
        }
      </ha-card>
    `;
  }

  _renderWasteItem(item) {
    const icon = this._getIcon(item.wasteType);
    const daysClass = item.isToday ? 'today' : (item.isTomorrow ? 'tomorrow' : '');
    const daysText = item.isToday ? 'Today!' : (item.isTomorrow ? 'Tomorrow' : `${item.daysUntil} days`);
    
    return `
      <div class="waste-item">
        <div class="waste-icon ${item.wasteType}">
          ${icon}
        </div>
        <div class="waste-info">
          <div class="waste-name">${this._formatWasteType(item.wasteType)}</div>
          <div class="waste-date">${item.formattedDate || item.date}</div>
        </div>
        <div class="days-until">
          <div class="days-number ${daysClass}">${item.daysUntil !== undefined ? item.daysUntil : '-'}</div>
          <div class="days-label">${item.daysUntil !== undefined ? daysText : ''}</div>
        </div>
      </div>
    `;
  }

  _getIcon(wasteType) {
    const icons = {
      'rubbish': '🗑️',
      'recycle': '♻️',
      'food-waste': '🍎'
    };
    return icons[wasteType] || '📦';
  }

  _formatWasteType(wasteType) {
    const names = {
      'rubbish': 'Rubbish',
      'recycle': 'Recycling',
      'food-waste': 'Food Waste'
    };
    return names[wasteType] || wasteType;
  }

  _getEntitiesByAreaNumber() {
    if (!this.config.area_number) return [];
    
    const areaNumber = this.config.area_number;
    const entities = [];
    
    // Find entities that match the area number
    for (const entityId of Object.keys(this._hass.states)) {
      if (entityId.startsWith('sensor.auckland_waste_')) {
        const state = this._hass.states[entityId];
        if (state.attributes.area_number === areaNumber) {
          entities.push(entityId);
        }
      }
    }
    
    return entities;
  }
}

// Register the card
customElements.define('auckland-waste-card', AucklandWasteCard);

// Register with Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'auckland-waste-card',
  name: 'Auckland Waste Card',
  description: 'A card to display Auckland waste collection days',
  preview: true
});

console.info(
  '%c AUCKLAND-WASTE-CARD %c v1.0.0 ',
  'color: white; background: #ef5350; font-weight: bold;',
  'color: #ef5350; background: white; font-weight: bold;'
);
