"use client";

import { RecommendationResponse, LocationDetail } from "../lib/api";
import { AlertTriangle, Info, ShieldAlert, Activity, CheckCircle2, Waves } from "lucide-react";

interface ReasoningPanelProps {
  locationDetail: LocationDetail | null;
  recommendation: RecommendationResponse | null;
  isLoading: boolean;
}

interface EvidenceChain {
  target_location?: string;
  target_uri?: string;
  hazard_status?: string;
  hazard_evidence?: {
    value: number;
    unit: string;
    status: string;
    date: string;
    source: string;
  }[];
  exposure_evidence?: {
    total_assets: number;
    population_at_risk: number;
    assets: {
      name: string;
      type: string;
      population: number;
      value_usd: number;
    }[];
  };
  vulnerability_evidence?: {
    indicator: string;
    value: number;
    unit: string;
  }[];
  mitigation_actions?: {
    action: string;
    description: string;
  }[];
}

export default function ReasoningPanel({
  locationDetail,
  recommendation,
  isLoading,
}: ReasoningPanelProps) {
  if (isLoading) {
    return (
      <div className="h-full bg-[#f3f8f7] border-l border-[#bbd9d4] p-6 flex items-center justify-center">
        <div className="flex flex-col items-center text-[#355f5d]">
          <div className="w-8 h-8 border-4 border-[#2f7a77] border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="animate-pulse">Running semantic reasoning engine...</p>
        </div>
      </div>
    );
  }

  if (!recommendation || !locationDetail) {
    return (
      <div className="h-full bg-[#f3f8f7] border-l border-[#bbd9d4] p-6 flex flex-col items-center justify-center text-[#355f5d] text-center">
        <ShieldAlert className="w-12 h-12 mb-4 text-[#2f7a77]" />
        <p>Select a location from the sidebar to run the early warning analysis.</p>
      </div>
    );
  }

  // Parse the reasoning chain JSON string
  let chain: EvidenceChain = {};
  try {
    chain = JSON.parse(recommendation.reasoning_chain);
  } catch (e) {
    console.error("Failed to parse reasoning chain", e);
  }

  const isCritical = recommendation.hazard_level === "critical";
  const isWarning = recommendation.hazard_level === "warning";

  const StatusIcon = isCritical ? AlertTriangle : isWarning ? Activity : CheckCircle2;
  const statusColor = isCritical ? "text-red-500" : isWarning ? "text-yellow-500" : "text-emerald-500";
  const bgStatus = isCritical ? "bg-red-500/10 border-red-500/20" : isWarning ? "bg-yellow-500/10 border-yellow-500/20" : "bg-emerald-500/10 border-emerald-500/20";

  return (
    <div className="h-full bg-[#f3f8f7] border-l border-[#bbd9d4] flex flex-col">
      {/* Header Panel */}
      <div className={`p-6 border-b border-[#d5e8e4] ${bgStatus}`}>
        <div className="flex items-center gap-3 mb-2">
          <StatusIcon className={`w-8 h-8 ${statusColor}`} />
          <div>
            <h2 className="text-xl font-bold text-[#143b3a] uppercase tracking-wider">
              {recommendation.hazard_level} Status
            </h2>
            <p className="text-sm text-[#355f5d]">Flood Hazard Alert</p>
          </div>
        </div>
        <p className="text-sm text-[#355f5d] mt-4 leading-relaxed font-medium">
          {recommendation.recommendation_text}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        
        {/* Exposure Summary */}
        <section>
          <h3 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-4 flex items-center gap-2">
            <Info className="w-4 h-4" /> Graph Evidence: Exposure
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-[#f7fcfa] p-4 rounded-xl border border-[#d5e8e4] shadow-sm">
              <div className="text-2xl font-bold text-[#143b3a] mb-1">
                {chain?.exposure_evidence?.total_assets || 0}
              </div>
              <div className="text-xs text-[#355f5d]">Critical Assets Exposed</div>
            </div>
            <div className="bg-[#f7fcfa] p-4 rounded-xl border border-[#d5e8e4] shadow-sm">
              <div className="text-2xl font-bold text-[#b43f3f] mb-1">
                {(chain?.exposure_evidence?.population_at_risk || 0).toLocaleString()}
              </div>
              <div className="text-xs text-[#355f5d]">Population at Risk</div>
            </div>
          </div>
        </section>

        {/* Hazard Observations */}
        {chain?.hazard_evidence && chain.hazard_evidence.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-4 flex items-center gap-2">
              <Waves className="w-4 h-4" /> Latest Graph Observations
            </h3>
            <div className="space-y-2">
              {chain.hazard_evidence.slice(0, 3).map((obs, i) => (
                <div key={i} className="flex justify-between items-center bg-[#f7fcfa] p-3 rounded-xl border border-[#d5e8e4] shadow-sm">
                  <div className="text-sm text-[#355f5d]">{obs.source}</div>
                  <div className={`text-sm font-bold ${obs.status === 'critical' ? 'text-red-400' : 'text-yellow-400'}`}>
                    {obs.value} {obs.unit}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Early Actions */}
        <section>
          <h3 className="text-xs font-semibold text-[#2f7a77] uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4" /> Recommended Early Actions
          </h3>
          <div className="space-y-3">
            {chain?.mitigation_actions?.map((action, idx) => (
              <div key={idx} className="bg-[#f7fcfa] p-4 rounded-xl border border-[#d5e8e4] border-l-2 border-l-[#2f7a77] shadow-sm">
                <h4 className="text-sm font-bold text-[#143b3a] mb-1">{action.action}</h4>
                <p className="text-xs text-[#355f5d] leading-relaxed">{action.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Raw Graph Link (Mock UI) */}
        <div className="pt-4 border-t border-[#d5e8e4]">
          <p className="text-xs text-[#4f7574] text-center">
            Reasoning sourced from <span className="font-mono bg-[#f7fcfa] px-1 py-0.5 rounded border border-[#d5e8e4]">kenya_pilot.ttl</span>
          </p>
        </div>

      </div>
    </div>
  );
}
