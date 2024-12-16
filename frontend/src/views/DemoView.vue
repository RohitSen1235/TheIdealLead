<!-- Template section remains the same -->
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
        <!-- ICP and Apply Section -->
        <div class="form-group">
          <label for="icp">Ideal Customer Profile</label>
          <div class="input-with-button">
            <textarea
              v-model="icp"
              id="icp"
              placeholder="Describe your ideal customer (e.g., 'Purchasing Managers in North America working in the Aerospace industry')"
              required
            ></textarea>
          </div>
        </div>

        <!-- Number of Leads and Apply Section -->
        <div class="form-group">
          <label for="numberOfLeads">Number of Leads</label>
          <div class="input-with-button">
            <input
              v-model.number="numberOfLeads"
              type="number"
              id="numberOfLeads"
              min="10"
              max="1000"
              placeholder="Enter number (10-1000)"
              required
            />
          </div>
        </div>

        <!-- Apply Button -->
        <button
          type="button"
          class="apply-button"
          :disabled="!canCalculateCredits"
          @click="calculateRequiredCredits"
        >
          Estimate Credit Requirement
        </button>

        <!-- Credit Information -->
        <div v-if="creditInfo" class="credit-info">
          <div class="credit-breakdown">
            <div class="complexity-info">
              <span>Complexity Multiple:</span>
              <span :class="getComplexityClass(creditInfo.complexity_multiple)">
                {{ creditInfo.complexity_multiple }}x
              </span>
            </div>
            <div class="credit-item">
              <span>Base Credits:</span>
              <span>{{ creditInfo.base_credits }}</span>
            </div>
            <div class="credit-item">
              <span>AI Processing:</span>
              <span>{{ creditInfo.ai_credits }}</span>
            </div>
          </div>
          <div class="credit-details">
            <div class="credit-item total">
              <span>Estimated Credits Required:</span>
              <span>{{ creditInfo.total_credits }}</span>
            </div>
          </div>
        </div>

        <button
          type="submit"
          class="cta-button"
          :disabled="isSubmitting || !creditInfo"
        >
          {{ isSubmitting ? "Starting Process..." : "Start Lead Generation" }}
        </button>
      </form>

      <!-- Task Progress Section -->
      <div v-else class="task-progress">
        <h3>Lead Generation Progress</h3>

        <!-- Status Display -->
        <div class="status-container">
          <!-- Main Status Message -->
          <div class="status-indicator" :class="groupStatus">
            {{ statusMessage }}
          </div>

          <!-- Progress Display -->
          <div class="progress-display">
            <div class="progress-bar">
              <div
                class="progress-bar-inner"
                :style="{ width: progressPercentage + '%' }"
                :class="{ partial: hasFailedTasks }"
              ></div>
            </div>
            <div class="progress-text">
              {{ totalLeadsFound }} of {{ totalLeadsNeeded }} profiles found
              <span v-if="hasFailedTasks" class="progress-warning">
                (some tasks failed)
              </span>
            </div>
          </div>

          <!-- Task Status Display -->
          <div v-if="taskStatuses" class="task-statuses">
            <div
              v-for="(status, taskId) in taskStatuses"
              :key="taskId"
              class="task-status"
              :class="status.toLowerCase()"
            >
              <span class="task-label">Task {{ getTaskNumber(taskId) }}</span>
              <span class="task-status-text">{{ status }}</span>
              <span
                v-if="getTaskError(taskId)"
                class="task-error-icon"
                :title="getTaskError(taskId)"
                >⚠️</span
              >
            </div>
          </div>

          <!-- Warning Display -->
          <div v-if="showWarnings && warnings.length" class="warning-section">
            <div
              v-for="(warning, index) in warnings"
              :key="index"
              class="warning-message"
            >
              {{ warning }}
            </div>
          </div>

          <!-- Error Display -->
          <div v-if="showErrors && errors.length" class="error-section">
            <div
              v-for="(error, index) in errors"
              :key="index"
              class="error-message"
            >
              {{ error }}
            </div>
          </div>

          <!-- Download Section -->
          <div v-if="canDownload" class="download-section">
            <p v-if="hasFailedTasks">
              Some tasks failed, but you can download the profiles that were
              found
            </p>
            <p v-else>Your leads are ready!</p>
            <button @click="downloadResults" class="download-button">
              Download {{ totalLeadsFound }} Leads (CSV)
            </button>
            <button
              v-if="hasFailedTasks"
              @click="retryFailedTasks"
              class="retry-button"
            >
              Retry Failed Tasks
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
      statusMessage: "",
      errors: [],
      warnings: [],
      statusCheckInterval: null,
      totalLeadsFound: 0,
      totalLeadsNeeded: 0,
      taskErrors: {},
      creditInfo: null,
    };
  },

  computed: {
    canCalculateCredits() {
      return (
        this.icp.trim() &&
        this.numberOfLeads >= 10 &&
        this.numberOfLeads <= 1000
      );
    },

    isProcessing() {
      return ["pending", "processing"].includes(this.groupStatus);
    },

    progressPercentage() {
      if (this.totalLeadsNeeded === 0) return 0;
      return Math.min(
        100,
        Math.round((this.totalLeadsFound / this.totalLeadsNeeded) * 100)
      );
    },

    showWarnings() {
      return !this.isProcessing && this.warnings.length > 0;
    },

    showErrors() {
      return !this.isProcessing && this.errors.length > 0;
    },

    hasFailedTasks() {
      return Object.values(this.taskStatuses || {}).includes("failed");
    },

    canDownload() {
      return (
        this.totalLeadsFound > 0 &&
        (!this.isProcessing ||
          (this.hasFailedTasks && this.totalLeadsFound > 0))
      );
    },
  },

  methods: {
    getComplexityClass(multiple) {
      if (multiple <= 1.5) return "complexity-low";
      if (multiple <= 3.0) return "complexity-medium";
      if (multiple <= 5.0) return "complexity-high";
      return "complexity-very-high";
    },

    async calculateRequiredCredits() {
      if (this.canCalculateCredits) {
        try {
          this.creditInfo = await api.calculateCredits(
            this.icp,
            this.numberOfLeads
          );
        } catch (error) {
          console.error("Error calculating credits:", error);
          this.creditInfo = null;
        }
      }
    },

    async startLeadGeneration() {
      if (!this.creditInfo) {
        return;
      }

      this.isSubmitting = true;
      this.errors = [];
      this.warnings = [];
      this.statusMessage = "Initializing lead generation...";
      this.taskErrors = {};

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
        this.statusMessage = status.status_message || "";
        this.totalLeadsFound = status.total_leads_found;
        this.totalLeadsNeeded = status.total_leads_needed;

        if (!this.isProcessing) {
          this.stopStatusChecking();
        }
      } catch (error) {
        console.error("Error checking task status:", error);
        this.errors = [error.message];
        this.stopStatusChecking();
      }
    },

    getTaskNumber(taskId) {
      const taskIds = Object.keys(this.taskStatuses);
      return taskIds.indexOf(taskId) + 1;
    },

    getTaskError(taskId) {
      return this.taskErrors[taskId] || "";
    },

    startStatusChecking() {
      this.statusCheckInterval = setInterval(() => {
        this.checkTaskStatus();
      }, 2000);
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

    async retryFailedTasks() {
      this.resetTask();
      await this.startLeadGeneration();
    },

    resetTask() {
      this.currentGroupId = null;
      this.groupStatus = "pending";
      this.taskStatuses = null;
      this.statusMessage = "";
      this.errors = [];
      this.warnings = [];
      this.totalLeadsFound = 0;
      this.totalLeadsNeeded = 0;
      this.taskErrors = {};
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

.apply-button {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
  width: 100%;
}

.apply-button:hover {
  background-color: #27ae60;
}

.apply-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
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
  width: 100%;
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
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.progress-display {
  margin: 1.5rem 0;
}

.progress-bar {
  height: 8px;
  background-color: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.progress-bar-inner {
  height: 100%;
  background-color: #4a90e2;
  transition: width 0.3s ease;
}

.progress-bar-inner.partial {
  background-color: #f39c12;
}

.progress-text {
  font-size: 1rem;
  color: #666;
  margin-top: 0.5rem;
}

.progress-warning {
  color: #f39c12;
  font-weight: 500;
  margin-left: 0.5rem;
}

.task-status {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  border-radius: 6px;
  background-color: #f8f9fa;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.task-label {
  flex: 0 0 auto;
  margin-right: 1rem;
}

.task-status-text {
  flex: 1;
}

.task-error-icon {
  flex: 0 0 auto;
  margin-left: 1rem;
  cursor: help;
}

.task-status.completed {
  background-color: #e8f5e9;
  color: #2e7d32;
}

.task-status.processing {
  background-color: #e3f2fd;
  color: #1976d2;
}

.task-status.failed {
  background-color: #fbe9e7;
  color: #d32f2f;
}

.task-status.pending {
  background-color: #f5f5f5;
  color: #757575;
}

.retry-button:hover {
  background-color: #c0392b;
}

.error-message {
  color: #e74c3c;
  background-color: #fde8e7;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.warning-message {
  color: #f39c12;
  background-color: #fef5e7;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.credit-info {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.credit-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.credit-item {
  display: flex;
  justify-content: space-between;
  color: #495057;
}

.credit-item.total {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #dee2e6;
  font-weight: bold;
  color: #2c3e50;
}

.credit-details {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #dee2e6;
}

.complexity-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.complexity-low {
  color: #28a745;
}

.complexity-medium {
  color: #ffc107;
}

.complexity-high {
  color: #fd7e14;
}

.complexity-very-high {
  color: #dc3545;
}

.credit-note {
  font-size: 0.875rem;
  color: #6c757d;
  text-align: center;
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
