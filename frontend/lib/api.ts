import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

export interface Location {
  id: number;
  name: string;
  admin_level: number;
  parent_id: number | null;
  latitude: number;
  longitude: number;
  geom_wkt: string;
  country_code: string;
}

export interface HazardObservation {
  id: number;
  hazard_type: string;
  observation_date: string;
  value: number;
  unit: string;
  source: string;
  status: string;
}

export interface Asset {
  id: number;
  name: string;
  asset_type: string;
  latitude: number;
  longitude: number;
  affected_population: number | null;
  estimated_value_usd: number | null;
}

export interface LocationDetail extends Location {
  observations: HazardObservation[];
  assets: Asset[];
}

export interface RecommendationResponse {
  location_id: number;
  hazard_level: string;
  recommendation_text: string;
  reasoning_chain: string; // JSON string
}

export const api = {
  getLocations: async (): Promise<Location[]> => {
    const response = await axios.get(`${API_BASE_URL}/locations/`);
    return response.data;
  },

  getLocationDetail: async (id: number): Promise<LocationDetail> => {
    const response = await axios.get(`${API_BASE_URL}/locations/${id}`);
    return response.data;
  },

  generateRecommendation: async (
    locationId: number,
    hazardType: string = "flood",
  ): Promise<RecommendationResponse> => {
    const response = await axios.post(
      `${API_BASE_URL}/recommendations/`,
      {
        location_id: locationId,
        hazard_type: hazardType,
      },
    );
    return response.data;
  },
};
