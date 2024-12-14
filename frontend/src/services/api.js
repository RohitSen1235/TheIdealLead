import axios from "axios";

const API_URL = "http://localhost:8000";

// Create a single axios instance with common configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add response interceptor for better error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", {
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
    });
    throw error;
  }
);

export default {
  async submitLead(leadData) {
    try {
      const response = await api.post("/submit-lead/", leadData);
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(error.response.data.message || "Server error occurred");
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to submit lead: " + error.message);
      }
    }
  },

  async startLeadGeneration(data) {
    try {
      const response = await api.post("/start-lead-generation/", data);
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to start lead generation"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to start lead generation: " + error.message);
      }
    }
  },

  async getTaskStatus(taskId) {
    try {
      const response = await api.get(`/task-status/${taskId}`);
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to get task status"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to get task status: " + error.message);
      }
    }
  },

  async downloadResults(taskId) {
    try {
      const response = await api.get(`/download-results/${taskId}`, {
        responseType: "blob",
      });

      // Get filename from Content-Disposition header if available
      let filename = "leads.csv";
      const disposition = response.headers["content-disposition"];
      if (disposition && disposition.includes("filename=")) {
        const filenameMatch = disposition.match(/filename=(.+)/);
        if (filenameMatch.length > 1) {
          filename = filenameMatch[1].replace(/["']/g, "");
        }
      }

      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);

      // Append to html link element page
      document.body.appendChild(link);

      // Start download
      link.click();

      // Clean up and remove the link
      link.parentNode.removeChild(link);
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to download results"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to download results: " + error.message);
      }
    }
  },
};
