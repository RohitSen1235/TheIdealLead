<template>
  <div>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Experience the power of AI-powered lead generation</h1>
        <p>
          Your journey to effective lead generation starts here. Fill out the
          form below to get started!
        </p>
      </div>
    </section>

    <!-- Lead Generation Form -->
    <div class="demo-container">
      <h2>Start Your Lead Generation Trial</h2>
      <p>
        Fill out the form below to initiate the lead generation process tailored
        to your Ideal Customer Profile.
        <br />
        <span class="note">
          Note: This is a demo version, so there are restrictions for usage.
        </span>
      </p>

      <!-- Form Section -->
      <form
        v-if="!currentGroupId"
        @submit.prevent="startLeadGeneration"
        class="lead-generation-form"
      >
        <div class="form-group">
          <label for="icp">Ideal Customer Profile</label>
          <textarea
            v-model="icp"
            id="icp"
            placeholder="Describe your ideal customer (e.g., 'Purchasing Managers in North America working in the Aerospace industry')"
            required
          ></textarea>
        </div>
        <div class="form-group">
          <label for="numberOfLeads">Number of Leads</label>
          <input
            v-model.number="numberOfLeads"
            type="number"
            id="numberOfLeads"
            min="1"
            max="200"
            placeholder="Enter number (1-200)"
            required
          />
        </div>
        <button type="submit" class="cta-button" :disabled="isSubmitting">
          {{ isSubmitting ? "Starting Process..." : "Start Lead Generation" }}
        </button>
      </form>

      <!-- Task Progress Section -->
      <div v-else class="task-progress">
        <h3>Lead Generation Progress</h3>

        <!-- Status Display -->
        <div class="status-container">
          <div class="status-indicator" :class="groupStatus">
            {{ getStatusMessage }}
          </div>

          <!-- Progress Display -->
          <div v-if="progressMessage" class="progress-message">
            {{ progressMessage }}
          </div>

          <!-- Task Status Display -->
          <div v-if="taskStatuses" class="task-statuses">
            <div
              v-for="(status, taskId) in taskStatuses"
              :key="taskId"
              class="task-status"
            >
              Task {{ getTaskNumber(taskId) }}: {{ status }}
            </div>
          </div>

          <!-- Progress Animation -->
          <div v-if="isProcessing" class="progress-bar">
            <div class="progress-bar-inner"></div>
          </div>

          <!-- Warning Display -->
          <div v-if="showWarnings && warnings.length" class="warning-section">
            <p
              v-for="(warning, index) in warnings"
              :key="index"
              class="warning-message"
            >
              {{ warning }}
            </p>
          </div>

          <!-- Error Display -->
          <div v-if="showErrors && errors.length" class="error-section">
            <p
              v-for="(error, index) in errors"
              :key="index"
              class="error-message"
            >
              {{ error }}
            </p>
            <button @click="resetTask" class="retry-button">Try Again</button>
          </div>

          <!-- Download Section -->
          <div v-if="groupStatus === 'completed'" class="download-section">
            <p>Your leads are ready!</p>
            <button @click="downloadResults" class="download-button">
              Download Leads (CSV)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";

export default {
  data() {
    return {
      icp: "",
      numberOfLeads: null,
      isSubmitting: false,
      currentGroupId: null,
      groupStatus: "pending",
      taskStatuses: null,
      progressMessage: "",
      errors: [],
      warnings: [],
      statusCheckInterval: null,
      totalLeadsFound: 0,
      totalLeadsNeeded: 0,
    };
  },

  computed: {
    isProcessing() {
      return ["pending", "processing"].includes(this.groupStatus);
    },

    getStatusMessage() {
      const messages = {
        pending: "Initializing lead generation...",
        processing: "Generating leads...",
        completed: "Lead generation completed!",
        failed: "Lead generation failed",
      };
      return messages[this.groupStatus] || "Unknown status";
    },

    showWarnings() {
      return !this.isProcessing;
    },

    showErrors() {
      return !this.isProcessing && this.groupStatus === "failed";
    },
  },

  methods: {
    async startLeadGeneration() {
      this.isSubmitting = true;
      this.errors = [];
      this.warnings = [];
      this.progressMessage = "";

      try {
        const response = await api.startLeadGeneration({
          ideal_customer_profile: this.icp,
          number_of_leads: this.numberOfLeads,
        });

        this.currentGroupId = response.group_id;
        this.startStatusChecking();
      } catch (error) {
        this.errors = [error.message];
      } finally {
        this.isSubmitting = false;
      }
    },

    async checkTaskStatus() {
      if (!this.currentGroupId) return;

      try {
        const status = await api.getTaskStatus(this.currentGroupId);
        this.groupStatus = status.status;
        this.taskStatuses = status.task_statuses;
        this.warnings = status.warnings || [];
        this.errors = status.errors || [];
        this.progressMessage = status.progress_message || "";
        this.totalLeadsFound = status.total_leads_found;
        this.totalLeadsNeeded = status.total_leads_needed;

        // Stop checking if group is completed or failed
        if (["completed", "failed"].includes(status.status)) {
          this.stopStatusChecking();
        }
      } catch (error) {
        console.error("Error checking task status:", error);
        this.errors = [error.message];
        this.stopStatusChecking();
      }
    },

    getTaskNumber(taskId) {
      // Get task number from task statuses object keys
      const taskIds = Object.keys(this.taskStatuses);
      return taskIds.indexOf(taskId) + 1;
    },

    startStatusChecking() {
      this.statusCheckInterval = setInterval(() => {
        this.checkTaskStatus();
      }, 2000); // Check every 2 seconds
    },

    stopStatusChecking() {
      if (this.statusCheckInterval) {
        clearInterval(this.statusCheckInterval);
        this.statusCheckInterval = null;
      }
    },

    async downloadResults() {
      try {
        await api.downloadResults(this.currentGroupId);
      } catch (error) {
        this.errors = [error.message];
      }
    },

    resetTask() {
      this.currentGroupId = null;
      this.groupStatus = "pending";
      this.taskStatuses = null;
      this.errors = [];
      this.warnings = [];
      this.progressMessage = "";
      this.totalLeadsFound = 0;
      this.totalLeadsNeeded = 0;
      this.stopStatusChecking();
    },
  },

  beforeUnmount() {
    this.stopStatusChecking();
  },
};
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #4a90e2 0%, #50e3c2 100%);
  color: white;
  padding: 4rem 2rem;
  text-align: center;
}

.hero-content h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.hero-content p {
  font-size: 1.2rem;
}

.demo-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  color: #333;
}

.note {
  color: #4a90e2;
  font-weight: bold;
}

h2,
h3 {
  text-align: center;
  margin-bottom: 1rem;
  color: #2c3e50;
}

h2 {
  font-size: 2rem;
}
h3 {
  font-size: 1.5rem;
}

.lead-generation-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
  color: #34495e;
}

textarea,
input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background-color: white;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

textarea:focus,
input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.cta-button,
.download-button,
.retry-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 1rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-button:hover,
.download-button:hover,
.retry-button:hover {
  background-color: #357abd;
  transform: translateY(-2px);
}

.cta-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.task-progress {
  text-align: center;
}

.status-container {
  margin-top: 2rem;
}

.status-indicator {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 1rem;
}

.progress-message {
  margin: 1rem 0;
  padding: 0.75rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  font-weight: 500;
}

.task-statuses {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.task-status {
  margin: 0.5rem 0;
  padding: 0.5rem;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  height: 4px;
  background-color: #eee;
  border-radius: 2px;
  overflow: hidden;
  margin: 1rem 0;
}

.progress-bar-inner {
  height: 100%;
  background-color: #4a90e2;
  animation: progress 2s infinite linear;
  transform-origin: 0% 50%;
}

@keyframes progress {
  0% {
    transform: translateX(0) scaleX(0);
  }
  40% {
    transform: translateX(0) scaleX(0.4);
  }
  100% {
    transform: translateX(100%) scaleX(0.5);
  }
}

.download-section,
.error-section,
.warning-section {
  margin-top: 2rem;
}

.download-button {
  background-color: #27ae60;
}

.download-button:hover {
  background-color: #219a52;
}

.retry-button {
  background-color: #e74c3c;
}

.retry-button:hover {
  background-color: #c0392b;
}

.error-message {
  color: #e74c3c;
  background-color: #fde8e7;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.warning-message {
  color: #f39c12;
  background-color: #fef5e7;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .demo-container {
    margin: 1rem;
    padding: 1.5rem;
  }

  .hero-content h1 {
    font-size: 2rem;
  }
}
</style>
