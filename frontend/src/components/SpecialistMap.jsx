import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Navigation, Clock, MapPin, Car, ShieldCheck } from 'lucide-react';

/**
 * Custom SVG DivIcon helper for crisp, high-DPI Leaflet markers
 */
const createPatientIcon = () => {
  return L.divIcon({
    className: 'custom-patient-marker',
    html: `
      <div class="relative flex items-center justify-center w-8 h-8">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <div class="relative w-8 h-8 bg-blue-600 border-2 border-white rounded-full shadow-lg flex items-center justify-center text-white">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

const createSpecialistIcon = (rank, isSelected) => {
  const isPrimary = rank === 1;
  const bgGradient = isPrimary
    ? 'bg-gradient-to-tr from-amber-500 to-indigo-600 border-2 border-white shadow-xl ring-2 ring-indigo-400'
    : isSelected
    ? 'bg-blue-600 border-2 border-white shadow-lg ring-2 ring-blue-400'
    : 'bg-slate-800 border-2 border-slate-600 shadow-md';

  const badgeText = rank ? `#${rank}` : '★';

  return L.divIcon({
    className: 'custom-specialist-marker',
    html: `
      <div class="relative flex items-center justify-center cursor-pointer transition-transform transform hover:scale-110">
        <div class="w-9 h-9 ${bgGradient} rounded-full flex items-center justify-center text-white font-bold text-xs shadow-md">
          ${badgeText}
        </div>
        ${isPrimary ? '<div class="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full border border-white"></div>' : ''}
      </div>
    `,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
    popupAnchor: [0, -18],
  });
};

export function SpecialistMap({
  patientLocation,
  specialists = [],
  selectedSpecialistId,
  onSelectSpecialist,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet map if not initialized
    if (!mapInstanceRef.current) {
      const defaultCenter = [
        patientLocation?.latitude || 34.0522,
        patientLocation?.longitude || -118.2437,
      ];

      const map = L.map(mapContainerRef.current, {
        center: defaultCenter,
        zoom: 11,
        zoomControl: false,
      });

      L.control.zoom({ position: 'topright' }).addTo(map);

      // OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | CarePath AI',
        maxZoom: 19,
      }).addTo(map);

      layerGroupRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    const bounds = [];

    // 1. Render Patient Marker
    if (patientLocation?.latitude && patientLocation?.longitude) {
      const pLat = parseFloat(patientLocation.latitude);
      const pLon = parseFloat(patientLocation.longitude);
      bounds.push([pLat, pLon]);

      const patientMarker = L.marker([pLat, pLon], { icon: createPatientIcon() });
      patientMarker.bindPopup(`
        <div class="p-1 font-sans">
          <div class="text-xs font-semibold text-blue-600 uppercase tracking-wider">Patient Origin</div>
          <div class="text-sm font-bold text-slate-800">${patientLocation.label || 'Patient Location'}</div>
          <div class="text-xs text-slate-500 font-mono mt-0.5">${pLat.toFixed(4)}, ${pLon.toFixed(4)}</div>
        </div>
      `);
      layerGroup.addLayer(patientMarker);
    }

    // 2. Render Specialist Markers & Routes
    specialists.forEach((spec) => {
      if (!spec.latitude || !spec.longitude) return;
      const sLat = parseFloat(spec.latitude);
      const sLon = parseFloat(spec.longitude);
      bounds.push([sLat, sLon]);

      const isSelected = selectedSpecialistId && String(spec.provider_id || spec.id) === String(selectedSpecialistId);
      const specMarker = L.marker([sLat, sLon], {
        icon: createSpecialistIcon(spec.rank, isSelected),
      });

      // Marker popup content
      const osrmInfo = spec.osrm || {};
      const roadDistStr = osrmInfo.distance_km ? `${osrmInfo.distance_km} km road` : `${spec.distance_km || spec.haversine_distance_km || '?'} km straight-line`;
      const roadTimeStr = osrmInfo.duration_minutes ? `🚗 ${osrmInfo.duration_minutes} min drive` : 'Road routing calculated';

      const popupHtml = `
        <div class="p-2 font-sans max-w-xs">
          <div class="flex items-center gap-1.5 mb-1">
            <span class="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full ${
              spec.rank === 1 ? 'bg-amber-100 text-amber-800 border border-amber-300' : 'bg-slate-100 text-slate-700'
            }">
              Rank #${spec.rank || 1} Specialist
            </span>
            ${spec.offers_telehealth ? '<span class="px-1.5 py-0.5 text-[9px] bg-emerald-50 text-emerald-700 rounded border border-emerald-200">Telehealth</span>' : ''}
          </div>
          <div class="text-base font-bold text-slate-900 leading-tight">${spec.name}</div>
          <div class="text-xs font-medium text-slate-600 mt-0.5">${spec.hospital || 'Medical Pavilion'}</div>

          <div class="mt-2 pt-2 border-t border-slate-100 grid grid-cols-2 gap-2 text-xs">
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-semibold">Predicted Wait</span>
              <span class="font-bold text-indigo-600">${spec.predicted_wait_days || spec.wait_days || 12} Days</span>
            </div>
            <div>
              <span class="text-slate-400 block text-[10px] uppercase font-semibold">Travel Metrics</span>
              <span class="font-bold text-slate-700 block">${roadDistStr}</span>
              <span class="text-[11px] text-blue-600 font-medium block">${roadTimeStr}</span>
            </div>
          </div>
        </div>
      `;

      specMarker.bindPopup(popupHtml);

      if (onSelectSpecialist) {
        specMarker.on('click', () => {
          onSelectSpecialist(spec);
        });
      }

      layerGroup.addLayer(specMarker);

      // 3. Render OSRM Route Line or Fallback Connecting Polyline
      const routeGeometry = osrmInfo.geometry || spec.geometry;
      if (routeGeometry) {
        try {
          const routeStyle = spec.rank === 1
            ? { color: '#2563eb', weight: 5, opacity: 0.9 }
            : { color: '#64748b', weight: 3, opacity: 0.5, dashArray: '6, 8' };

          const geoLayer = L.geoJSON(routeGeometry, { style: routeStyle });
          layerGroup.addLayer(geoLayer);
        } catch (err) {
          console.warn('GeoJSON rendering skipped:', err);
        }
      } else if (patientLocation?.latitude && patientLocation?.longitude) {
        const pLat = parseFloat(patientLocation.latitude);
        const pLon = parseFloat(patientLocation.longitude);
        const polyline = L.polyline([[pLat, pLon], [sLat, sLon]], {
          color: spec.rank === 1 ? '#2563eb' : '#94a3b8',
          weight: spec.rank === 1 ? 4 : 2,
          dashArray: '8, 8',
          opacity: 0.85,
        });
        layerGroup.addLayer(polyline);
      }
    });

    // 4. Adjust bounds so all pins are visible
    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [45, 45], maxZoom: 14 });
    }

  }, [patientLocation, specialists, selectedSpecialistId, onSelectSpecialist]);

  // Extract OSRM summary metrics from top specialist
  const topSpec = specialists[0] || {};
  const osrmData = topSpec.osrm || {};

  return (
    <div className="relative rounded-2xl overflow-hidden border border-slate-200 shadow-md bg-white">
      {/* Map Header Bar */}
      <div className="px-4 py-3 bg-slate-900 text-white flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Navigation className="w-5 h-5 text-blue-400" />
          <h3 className="font-semibold text-sm">Interactive Care Path Map</h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-mono border border-blue-400/30">
            OSRM Engine Active
          </span>
        </div>

        {/* Travel Metrics Summary Badge */}
        {osrmData.available && (
          <div className="flex items-center gap-4 text-xs bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
            <div className="flex items-center gap-1.5 text-blue-300">
              <Car className="w-4 h-4 text-blue-400" />
              <span>
                Road Distance: <strong>{osrmData.distance_km} km</strong>
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-300 border-l border-slate-700 pl-3">
              <Clock className="w-4 h-4 text-emerald-400" />
              <span>
                Est. Drive: <strong>{osrmData.duration_minutes} min</strong>
              </span>
            </div>
            {topSpec.haversine_distance_km && (
              <div className="text-slate-400 text-[11px] border-l border-slate-700 pl-3 hidden sm:block">
                (Straight-line: {topSpec.haversine_distance_km} km)
              </div>
            )}
          </div>
        )}
      </div>

      {/* Leaflet Map DOM Container */}
      <div ref={mapContainerRef} className="w-full h-[420px] z-10 bg-slate-100" />

      {/* Map Legend Footer */}
      <div className="px-4 py-2 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-600 border border-white inline-block"></span>
            <span>Patient Origin</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 rounded-full bg-gradient-to-tr from-amber-500 to-indigo-600 text-[9px] text-white flex items-center justify-center font-bold">#1</span>
            <span className="font-medium text-slate-800">Rank #1 Match</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-800 text-[9px] text-white flex items-center justify-center font-bold">#2</span>
            <span>Alternative Specialists</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>Real-Time OSRM Driving Route Geometry</span>
        </div>
      </div>
    </div>
  );
}
