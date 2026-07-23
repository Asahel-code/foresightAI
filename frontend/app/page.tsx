"use client";

import { useState, useEffect } from "react";
import {
  api,
  Location,
  LocationDetail,
  RecommendationResponse,
} from "../lib/api";
import LocationSelector from "../components/LocationSelector";
import HazardMap from "../components/HazardMap";
import ReasoningPanel from "../components/ReasoningPanel";

export default function Home() {
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(
    null,
  );
  const [locationDetail, setLocationDetail] = useState<LocationDetail | null>(
    null,
  );
  const [recommendation, setRecommendation] =
    useState<RecommendationResponse | null>(null);

  const [isReasoningLoading, setIsReasoningLoading] = useState(false);

  const handleLocationSelect = async (location: Location) => {
    setSelectedLocation(location);
    setLocationDetail(null);
    setRecommendation(null);
    setIsReasoningLoading(true);

    try {
      // Fetch map detail (assets, bounds)
      const detail = await api.getLocationDetail(location.id);
      setLocationDetail(detail);

      // Trigger the semantic reasoning engine
      const rec = await api.generateRecommendation(location.id, "flood");
      setRecommendation(rec);
    } catch (error) {
      console.error("Failed to process location", error);
    } finally {
      setIsReasoningLoading(false);
    }
  };

  // Initial load: Fetch all pilot locations
  useEffect(() => {
    async function loadLocations() {
      try {
        const data = await api.getLocations();
        setLocations(data);

        // Auto-select Tana River County (id=2) if it exists, otherwise the first one
        if (data.length > 0) {
          const tanaRiver =
            data.find((l) => l.name === "Tana River County") || data[0];
          handleLocationSelect(tanaRiver);
        }
      } catch (error) {
        console.error("Failed to load locations", error);
      }
    }
    loadLocations();
  }, []);

  return (
    <main className="h-screen w-full flex overflow-hidden">
      {/* Left Sidebar: Location Selection */}
      <aside className="w-80 h-full flex-shrink-0 z-20">
        <LocationSelector
          locations={locations}
          selectedLocation={selectedLocation}
          onSelect={handleLocationSelect}
        />
      </aside>

      {/* Center Panel: MapLibre Interactive Map */}
      <section className="flex-1 h-full relative z-10">
        <HazardMap
          locationDetail={locationDetail}
          selectedLocation={selectedLocation}
        />
      </section>

      {/* Right Sidebar: Semantic Reasoning & Recommendations */}
      <aside className="w-[450px] h-full flex-shrink-0 z-20 shadow-[-10px_0_15px_-3px_rgba(0,0,0,0.5)]">
        <ReasoningPanel
          locationDetail={locationDetail}
          recommendation={recommendation}
          isLoading={isReasoningLoading}
        />
      </aside>
    </main>
  );
}
