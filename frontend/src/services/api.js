import axios from "axios";

const API_URL = "http://localhost:8000";

// Create a single axios instance with common configuration
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

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

    // If unauthorized, clear token and redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/auth";
    }

    return Promise.reject(error);
  }
);

export default {
  async register(userData) {
    try {
      const response = await api.post("/register", userData);
      if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
      }
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(error.response.data.message || "Registration failed");
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to register: " + error.message);
      }
    }
  },

  async login(email, password) {
    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);

      // Create a new config for this specific request
      const config = {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      };

      // Convert FormData to URLSearchParams
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const response = await api.post("/token", params, config);
      if (response.data.access_token) {
        localStorage.setItem("access_token", response.data.access_token);
      }
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(error.response.data.message || "Login failed");
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to login: " + error.message);
      }
    }
  },

  async getUserProfile() {
    try {
      const response = await api.get("/users/me");
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to get user profile"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to get user profile: " + error.message);
      }
    }
  },

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

  async calculateCredits(icp, numLeads) {
    try {
      const response = await api.post("/calculate-credits/", {
        ideal_customer_profile: icp,
        number_of_leads: numLeads,
      });
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to calculate credits"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to calculate credits: " + error.message);
      }
    }
  },

  async startLeadGeneration(data) {
    try {
      const response = await api.post("/start-lead-generation/", {
        ideal_customer_profile: data.ideal_customer_profile,
        number_of_leads: data.number_of_leads,
        get_work_email: data.get_work_email,
        get_phone_number: data.get_phone_number,
      });
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

  async purchaseCredits(credits) {
    try {
      const response = await api.post("/purchase-credits/", { credits });
      return response.data;
    } catch (error) {
      if (error.response) {
        throw new Error(
          error.response.data.message || "Failed to purchase credits"
        );
      } else if (error.request) {
        throw new Error(
          "No response from server. Please check your connection."
        );
      } else {
        throw new Error("Failed to purchase credits: " + error.message);
      }
    }
  },

  logout() {
    localStorage.removeItem("access_token");
    window.location.href = "/auth";
  },
};
