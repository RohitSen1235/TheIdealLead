import axios from "axios";

const API_URL = "http://localhost:8000"; // Replace with your backend URL

const api = axios.create({
  baseURL: "http://localhost:8000", // Ensure this matches your backend URL
});

export default {
  async submitLead(leadData) {
    try {
      const response = await axios.post(`${API_URL}/submit-lead/`, leadData, {
        headers: {
          "Content-Type": "application/json",
        },
      });
      return response.data;
    } catch (error) {
      console.error(
        "Error submitting lead:",
        error.response ? error.response.data : error.message
      );
      throw error;
    }
  },
  async startLeadGeneration(data) {
    const response = await api.post("/start-lead-generation/", data);
    // return api.post("/start-lead-generation/", data);
    return response.data;
  },
};
