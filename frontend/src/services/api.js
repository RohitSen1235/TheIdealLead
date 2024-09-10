import axios from "axios";

const API_URL = "http://localhost:8000"; // Replace with your backend URL

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
};
