"use client";

import { Location } from "../lib/api";
import { MapPin, Navigation } from "lucide-react";

interface LocationSelectorProps {
  locations: Location[];
  selectedLocation: Location | null;
  onSelect: (location: Location) => void;
}

export default function LocationSelector({
  locations,
  selectedLocation,
  onSelect,
}: LocationSelectorProps) {
  // Group by admin level for nicer display
  const countries = locations.filter((l) => l.admin_level === 0);
  const counties = locations.filter((l) => l.admin_level === 1);
  const subCounties = locations.filter((l) => l.admin_level === 2);

  const renderLocation = (loc: Location, icon: React.ReactNode) => {
    const isSelected = selectedLocation?.id === loc.id;
    return (
      <button
        key={loc.id}
        onClick={() => onSelect(loc)}
        className={`w-full text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all border ${
          isSelected
            ? "bg-[#1f6f6b] text-white shadow-md border-[#1f6f6b]"
            : "hover:bg-[#e7f4ef] text-[#355f5d] border-transparent"
        }`}
      >
        <div className={isSelected ? "text-[#e7f4ef]" : "text-[#2f7a77]"}>
          {icon}
        </div>
        <div className="flex-1">
          <div className="font-medium text-sm">{loc.name}</div>
        </div>
      </button>
    );
  };

  return (
    <div className="h-full bg-[#f3f8f7] border-r border-[#bbd9d4] flex flex-col">
      <div className="p-6 border-b border-[#d5e8e4] bg-[#f7fcfa]">
        <h1 className="text-xl font-bold text-[#143b3a] flex items-center gap-2">
          <Navigation className="w-5 h-5 text-[#2f7a77]" />
          ForeSightAI
        </h1>
        <p className="text-sm text-[#355f5d] mt-1">
          Pilot Early Warning System
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <div>
          <h2 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-3 px-2">
            Country Overview
          </h2>
          <div className="space-y-1">
            {countries.map((l) => renderLocation(l, <MapPin className="w-4 h-4" />))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-3 px-2">
            Counties
          </h2>
          <div className="space-y-1">
            {counties.map((l) => renderLocation(l, <MapPin className="w-4 h-4" />))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-3 px-2">
            Sub-Counties
          </h2>
          <div className="space-y-1">
            {subCounties.map((l) => renderLocation(l, <MapPin className="w-4 h-4" />))}
          </div>
        </div>
      </div>
    </div>
  );
}
