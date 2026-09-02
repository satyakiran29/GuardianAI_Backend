// GuardianAI Dashboard Interactive Logic with OpenFreeMap Integration
let liveMap = null;
let markersLayer = null;

document.addEventListener('DOMContentLoaded', () => {
  initLiveMap();
  initAutoRefresh();
  initOtpSimulator();
});

// Initialize Leaflet Interactive Map using OpenFreeMap (100% Free, Zero Key, Fast Vector & Raster Tiles)
function initLiveMap() {
  const mapElement = document.getElementById('live-map');
  if (!mapElement) return;

  if (liveMap) {
    liveMap.remove();
    liveMap = null;
  }

  // Center on default city coordinates (Hyderabad / India)
  liveMap = L.map('live-map', {
    zoomControl: true,
    attributionControl: true
  }).setView([17.4065, 78.4772], 12);

  // OpenFreeMap Free Dark Tiles Layer (No API Key Required)
  const openFreeMapDark = L.tileLayer('https://tiles.openfreemap.org/styles/dark/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://openfreemap.org" target="_blank" style="color: #60a5fa; text-decoration: none;">OpenFreeMap</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" style="color: #64748b;">OpenStreetMap</a> contributors'
  });

  // OpenFreeMap Free Liberty / High-Detail Street Tiles Layer
  const openFreeMapLiberty = L.tileLayer('https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://openfreemap.org" target="_blank" style="color: #60a5fa; text-decoration: none;">OpenFreeMap</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" style="color: #64748b;">OpenStreetMap</a> contributors'
  });

  // OpenFreeMap Bright / High-Contrast Layer
  const openFreeMapBright = L.tileLayer('https://tiles.openfreemap.org/styles/bright/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://openfreemap.org" target="_blank" style="color: #60a5fa; text-decoration: none;">OpenFreeMap</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" style="color: #64748b;">OpenStreetMap</a> contributors'
  });

  // Add default dark layer
  openFreeMapDark.addTo(liveMap);

  // Add layer controls for easy switching between free OpenFreeMap styles
  const baseMaps = {
    "🌌 OpenFreeMap Dark Radar": openFreeMapDark,
    "🏙️ OpenFreeMap Liberty Street": openFreeMapLiberty,
    "☀️ OpenFreeMap Bright Mode": openFreeMapBright
  };
  L.control.layers(baseMaps, null, { position: 'topright' }).addTo(liveMap);

  markersLayer = L.layerGroup().addTo(liveMap);

  renderMapMarkers();
}

function renderMapMarkers() {
  if (!markersLayer || typeof MAP_MARKERS === 'undefined') return;

  markersLayer.clearLayers();
  const bounds = [];

  MAP_MARKERS.forEach(item => {
    if (!item.lat || !item.lng) return;

    bounds.push([item.lat, item.lng]);

    if (item.type === 'alert') {
      // Red Radar Pulse Marker for Active SOS
      const pulseHtml = `
        <div class="radar-pulse-marker">
          <div class="wave"></div>
          <div class="core"></div>
        </div>
      `;

      const pulseIcon = L.divIcon({
        className: 'custom-radar-icon',
        html: pulseHtml,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });

      const popupContent = `
        <div style="color: #0f172a; font-family: sans-serif; min-width: 220px;">
          <h4 style="margin: 0 0 6px; color: #ef4444; font-size: 14px; font-weight: bold;">🚨 SOS #${item.id} - ${item.status.toUpperCase()}</h4>
          <p style="margin: 0 0 4px; font-size: 12px;"><strong>Victim:</strong> ${item.user_name} (<code>${item.user_phone}</code>)</p>
          <p style="margin: 0 0 4px; font-size: 12px;"><strong>Trigger:</strong> ${item.trigger_source}</p>
          <p style="margin: 0 0 4px; font-size: 12px;"><strong>Battery:</strong> ${item.battery}%</p>
          <p style="margin: 0 0 8px; font-size: 11px; color: #475569;">📍 ${item.address}</p>
          <div style="display: flex; gap: 6px; margin-top: 6px;">
            <a href="/alerts/" style="background: #ef4444; color: #fff; padding: 4px 10px; text-decoration: none; border-radius: 4px; font-size: 11px; font-weight: bold;">⚡ Dispatch Unit</a>
          </div>
        </div>
      `;

      const marker = L.marker([item.lat, item.lng], { icon: pulseIcon }).bindPopup(popupContent);
      markersLayer.addLayer(marker);

      // Add emergency zone pulsing radius
      L.circle([item.lat, item.lng], {
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.15,
        radius: 450
      }).addTo(markersLayer);

    } else if (item.type === 'guardian') {
      // Emerald Shield Marker for Guardian Responders
      const guardHtml = `
        <div style="background: #10b981; border: 2px solid #fff; border-radius: 50%; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; box-shadow: 0 0 10px #10b981;">
          🛡️
        </div>
      `;

      const guardIcon = L.divIcon({
        className: 'custom-guard-icon',
        html: guardHtml,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const guardPopup = `
        <div style="color: #0f172a; font-family: sans-serif; min-width: 180px;">
          <h4 style="margin: 0 0 4px; color: #10b981; font-size: 13px; font-weight: bold;">🛡️ Guardian Unit</h4>
          <p style="margin: 0 0 2px; font-size: 12px;"><strong>${item.name}</strong></p>
          <p style="margin: 0 0 4px; font-size: 11px; color: #475569;">📞 ${item.phone}</p>
          <p style="margin: 0; font-size: 11px; color: #64748b;">📍 ${item.address || 'Patrol Route'}</p>
        </div>
      `;

      const marker = L.marker([item.lat, item.lng], { icon: guardIcon }).bindPopup(guardPopup);
      markersLayer.addLayer(marker);
    }
  });

  if (bounds.length > 0) {
    liveMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }
}

// Live Polling for Telemetry & Alert Feed
function initAutoRefresh() {
  setInterval(async () => {
    try {
      const response = await fetch('/api/dashboard/stats/');
      if (response.ok) {
        const data = await response.json();
        
        // Update header counters if elements exist
        const sosCountEl = document.getElementById('stat-active-sos');
        if (sosCountEl) sosCountEl.innerText = data.active_alerts;
        
        const totalUsersEl = document.getElementById('stat-total-users');
        if (totalUsersEl) totalUsersEl.innerText = data.total_users;
      }
    } catch (e) {
      console.debug('Polling tick notice:', e);
    }
  }, 10000);
}

// OTP Simulator helper
function initOtpSimulator() {
  const btnSendTestOtp = document.getElementById('btn-send-test-otp');
  if (!btnSendTestOtp) return;

  btnSendTestOtp.addEventListener('click', async () => {
    const targetInput = document.getElementById('test-otp-target');
    const target = targetInput ? targetInput.value.trim() : '';
    const outputDiv = document.getElementById('test-otp-result');

    if (!target) {
      alert('Please enter a phone number or email address');
      return;
    }

    try {
      btnSendTestOtp.disabled = true;
      btnSendTestOtp.innerText = 'Dispatching OTP...';

      const res = await fetch('/api/auth/send-otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: target, purpose: 'dashboard_test' })
      });

      const json = await res.json();
      btnSendTestOtp.disabled = false;
      btnSendTestOtp.innerText = 'Send Test OTP';

      if (outputDiv) {
        outputDiv.innerHTML = `
          <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; padding: 12px; border-radius: 8px; margin-top: 10px; color: #34d399;">
            <strong>✅ OTP Dispatched!</strong><br>
            Target: <code>${json.target}</code><br>
            Generated Code: <strong style="font-size: 1.2rem; color: #fff; letter-spacing: 2px;">${json.otp}</strong><br>
            Expires in: 10 Minutes
          </div>
        `;
      }
    } catch (e) {
      btnSendTestOtp.disabled = false;
      btnSendTestOtp.innerText = 'Send Test OTP';
      alert('Error sending OTP: ' + e);
    }
  });
}

// Modal Toggle Helpers
function openModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.add('active');
}

function closeModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove('active');
}
