
import api from "../config/api";

export const getLeadOptions = async () => {
  const response = await api.get("/options");

  return response.data;
};

export const getLeads = async (filters = {}) => {
  const response = await api.get("/leads", {
    params: filters,
  });

  return response.data;
};
