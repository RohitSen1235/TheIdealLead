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
    // If the error response is a blob (failed download), convert it to JSON
    if (error.response?.data instanceof Blob) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            error.response.data = JSON.parse(reader.result);
            reject(error);
          } catch (e) {
            error.response.data = { message: "Failed to parse error response" };
            reject(error);
          }
        };
        reader.onerror = () => {
          error.response.data = { message: "Failed to read error response" };
          reject(error);
        };
        reader.readAsText(error.response.data);
      });
    }
    return Promise.reject(error);
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

  async getTaskStatus(groupId) {
    try {
      const response = await api.get(`/task-status/${groupId}`);
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

  async downloadResults(groupId) {
    try {
      const response = await api.get(`/download-results/${groupId}`, {
        responseType: "blob",
      });

      // Check if the response is actually an error (non-blob)
      const contentType = response.headers["content-type"];
      if (contentType && !contentType.includes("text/csv")) {
        throw new Error("Invalid response format");
      }

      // Get filename from Content-Disposition header if available
      let filename = "leads.csv";
      const disposition = response.headers["content-disposition"];
      if (disposition && disposition.includes("filename=")) {
        const filenameMatch = disposition.match(/filename=(.+)/);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1].replace(/["']/g, "");
        }
      }

      // Create blob link to download
      const url = window.URL.createObjectURL(
        new Blob([response.data], { type: "text/csv" })
      );
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);

      // Append to html link element page
      document.body.appendChild(link);

      // Start download
      link.click();

      // Clean up and remove the link
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      if (error.response) {
        // Try to parse error message from response
        const errorMessage =
          error.response.data?.message || "Failed to download results";
        throw new Error(errorMessage);
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
