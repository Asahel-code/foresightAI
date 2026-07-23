"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { LocationDetail, Location } from "../lib/api";

interface HazardMapProps {
  locationDetail: LocationDetail | null;
  selectedLocation: Location | null;
}

export default function HazardMap({
  locationDetail,
  selectedLocation,
}: HazardMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [mapStatus, setMapStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [mapError, setMapError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    if (map.current) return;

    try {
      const mapInstance = new maplibregl.Map({
        container: mapContainer.current,
        style:
          "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json",
        center: [38.0, 0.0], // Default center (Kenya roughly)
        zoom: 5,
        attributionControl: false,
      });

      map.current = mapInstance;
      mapInstance.addControl(new maplibregl.NavigationControl(), "top-right");

      mapInstance.on("load", () => {
        setMapStatus("ready");
        setMapError(null);
      });

      mapInstance.on("error", () => {
        setMapStatus("error");
        setMapError("The map could not be initialized in this browser.");
      });
    } catch (error) {
      console.error("MapLibre failed to initialize", error);
      queueMicrotask(() => {
        setMapStatus("error");
        setMapError("The map could not be initialized in this browser.");
      });
    }

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
      setMapStatus("loading");
      setMapError(null);
    };
  }, []);

  // Update map center and markers when data changes
  useEffect(() => {
    if (!map.current || !selectedLocation || mapStatus !== "ready") return;

    // Fly to location
    map.current.flyTo({
      center: [selectedLocation.longitude, selectedLocation.latitude],
      zoom:
        selectedLocation.admin_level === 0
          ? 5
          : selectedLocation.admin_level === 1
            ? 7
            : 9,
      essential: true,
    });

    // Clear old markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Add new markers if detail is loaded
    if (locationDetail?.assets) {
      locationDetail.assets.forEach((asset) => {
        // Create custom marker element based on type
        const el = document.createElement("div");
        el.className =
          "w-4 h-4 rounded-full border-2 border-slate-900 shadow-md";

        if (asset.asset_type === "river_gauge") {
          el.classList.add("bg-blue-400");
        } else if (asset.asset_type === "hospital") {
          el.classList.add("bg-red-500");
        } else if (asset.asset_type === "school") {
          el.classList.add("bg-yellow-400");
        } else if (asset.asset_type === "bridge") {
          el.classList.add("bg-slate-400");
        } else {
          el.classList.add("bg-emerald-500");
        }

        const popupHTML = `
          <div class="text-slate-900 p-1">
            <div class="font-bold text-sm mb-1">${asset.name}</div>
            <div class="text-xs capitalize text-slate-500">${asset.asset_type.replace("_", " ")}</div>
            ${asset.affected_population ? `<div class="text-xs mt-1"><span class="font-semibold">Pop:</span> ${asset.affected_population.toLocaleString()}</div>` : ""}
            ${asset.estimated_value_usd ? `<div class="text-xs"><span class="font-semibold">Value:</span> $${asset.estimated_value_usd.toLocaleString()}</div>` : ""}
          </div>
        `;

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([asset.longitude, asset.latitude])
          .setPopup(new maplibregl.Popup({ offset: 15 }).setHTML(popupHTML))
          .addTo(map.current!);

        markersRef.current.push(marker);
      });
    }
  }, [locationDetail, mapStatus, selectedLocation]);

  return (
    <div className="relative w-full h-full bg-[#f3f8f7]">
      <div
        ref={mapContainer}
        className={`absolute inset-0 ${mapStatus === "ready" ? "block" : "hidden"}`}
      />

      {mapStatus !== "ready" && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#f3f8f7]/95 text-[#173d3c]">
          <div className="mx-6 max-w-md rounded-2xl border border-[#bbd9d4] bg-[#f7fcfa] p-6 shadow-[0_12px_35px_rgba(20,70,72,0.14)]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-[#2f7a77]">
              {mapStatus === "loading" ? "Loading map" : "Map preview unavailable"}
            </p>
            <h3 className="mt-2 text-xl font-semibold text-[#143b3a]">
              {selectedLocation?.name ?? "Selected location"}
            </h3>
            <p className="mt-2 text-sm text-[#355f5d]">
              {selectedLocation
                ? `${selectedLocation.latitude.toFixed(3)}, ${selectedLocation.longitude.toFixed(3)}`
                : "Choose a location to view the hazard map."}
            </p>
            <p className="mt-4 text-sm text-[#4f7574]">
              {mapError ??
                "The browser could not create a WebGL context for the map."}
            </p>
          </div>
        </div>
      )}

      {/* Legend overlay */}
      <div className="absolute bottom-6 right-10 border border-[#bbd9d4] bg-[#f7fcfa]/95 p-4 rounded-2xl shadow-[0_10px_25px_rgba(20,70,72,0.12)] backdrop-blur-sm z-10 text-xs">
        <h3 className="text-[#215d5a] font-semibold mb-3 uppercase tracking-[0.2em]">
          Asset Legend
        </h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#d9534f] border border-[#8a2f2a]"></div>
            <span className="text-[#355f5d]">Hospital</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#f2b84b] border border-[#a56d16]"></div>
            <span className="text-[#355f5d]">School</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#2f7ecf] border border-[#21588f]"></div>
            <span className="text-[#355f5d]">River Gauge</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#6c7b6b] border border-[#4a584d]"></div>
            <span className="text-[#355f5d]">Bridge</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#2f9e65] border border-[#1f6b45]"></div>
            <span className="text-[#355f5d]">Agriculture / Other</span>
          </div>
        </div>
      </div>
    </div>
  );
}
