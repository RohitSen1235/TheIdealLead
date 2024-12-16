<template>
  <div>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>AI-Powered Lead Generation</h1>
        <p>
          Generate high-quality leads tailored to your Ideal Customer Profile
        </p>
        <div class="user-info" v-if="user">
          <p>Welcome, {{ user.name }}</p>
          <p class="credits">
            Available Credits: {{ user.credits }}
            <button
              @click="showPurchaseModal = true"
              class="purchase-credits-btn"
            >
              Purchase Credits
            </button>
          </p>
        </div>
      </div>
    </section>

    <!-- Credit Purchase Modal -->
    <div v-if="showPurchaseModal" class="modal-overlay">
      <div class="modal">
        <h2>Purchase Credits</h2>
        <div class="credit-packages">
          <div
            v-for="pkg in creditPackages"
            :key="pkg.credits"
            class="credit-package"
            :class="{ selected: selectedPackage === pkg }"
            @click="selectedPackage = pkg"
          >
            <h3>{{ pkg.credits }} Credits</h3>
            <p class="price">${{ pkg.price }}</p>
            <p class="savings" v-if="pkg.savings">Save {{ pkg.savings }}%</p>
          </div>
        </div>
        <div class="modal-actions">
          <button
            class="purchase-button"
            :disabled="!selectedPackage || isPurchasing"
            @click="purchaseCredits"
          >
            {{
              isPurchasing
                ? "Processing..."
                : `Purchase ${selectedPackage?.credits || ""} Credits`
            }}
          </button>
          <button class="cancel-button" @click="showPurchaseModal = false">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Lead Generation Form -->
    <div class="demo-container">
      <h2>Generate Targeted Leads</h2>
      <p>
        Fill out the form below to initiate the lead generation process tailored
        to your Ideal Customer Profile.
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

        <!-- Optional Services Section -->
        <div class="optional-services">
          <h3>Optional Value-Added Services</h3>
          <div class="service-options">
            <div class="service-option">
              <input type="checkbox" id="workEmail" v-model="getWorkEmail" />
              <label for="workEmail">
                Get Work Email
                <span class="service-description"> (+2 credits per lead) </span>
              </label>
            </div>
            <div class="service-option">
              <input
                type="checkbox"
                id="phoneNumber"
                v-model="getPhoneNumber"
              />
              <label for="phoneNumber">
                Get Phone Number
                <span class="service-description"> (+3 credits per lead) </span>
              </label>
            </div>
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
            <div v-if="getWorkEmail" class="credit-item">
              <span>Work Email Service:</span>
              <span>{{ workEmailCredits }}</span>
            </div>
            <div v-if="getPhoneNumber" class="credit-item">
              <span>Phone Number Service:</span>
              <span>{{ phoneNumberCredits }}</span>
            </div>
          </div>
          <div class="credit-details">
            <div class="credit-item total">
              <span>Estimated Credits Required:</span>
              <span>{{ creditInfo.total_credits }}</span>
            </div>
            <div
              v-if="user && creditInfo.total_credits > user.credits"
              class="insufficient-credits"
            >
              Insufficient credits. You need
              {{ creditInfo.total_credits - user.credits }} more credits.
            </div>
          </div>
        </div>

        <!-- Rest of the form remains the same -->
        <button
          type="submit"
          class="cta-button"
          :disabled="
            isSubmitting ||
            !creditInfo ||
            (user && creditInfo.total_credits > user.credits)
          "
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
import api from "@/services/api.js";

export default {
  data() {
    return {
      user: null,
      icp: "",
      numberOfLeads: null,
      getWorkEmail: false,
      getPhoneNumber: false,
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
      showPurchaseModal: false,
      selectedPackage: null,
      isPurchasing: false,
      creditPackages: [
        { credits: 100, price: 49, savings: null },
        { credits: 500, price: 199, savings: 20 },
        { credits: 1000, price: 349, savings: 30 },
      ],
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

    workEmailCredits() {
      return this.getWorkEmail ? this.numberOfLeads * 2 : 0;
    },

    phoneNumberCredits() {
      return this.getPhoneNumber ? this.numberOfLeads * 3 : 0;
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
      if (multiple <= 1.2) return "complexity-low";
      if (multiple <= 1.5) return "complexity-medium";
      if (multiple <= 2) return "complexity-high";
      return "complexity-very-high";
    },

    async calculateRequiredCredits() {
      if (this.canCalculateCredits) {
        try {
          this.creditInfo = await api.calculateCredits(
            this.icp,
            this.numberOfLeads
          );
          // Add additional credits for optional services
          this.creditInfo.total_credits +=
            this.workEmailCredits + this.phoneNumberCredits;
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
        const result = await api.startLeadGeneration({
          ideal_customer_profile: this.icp,
          number_of_leads: this.numberOfLeads,
          get_work_email: this.getWorkEmail,
          get_phone_number: this.getPhoneNumber,
        });

        this.currentGroupId = result.group_id;
        this.startStatusChecking();

        // Update user credits
        this.user = await api.getUserProfile();
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

    async purchaseCredits() {
      if (!this.selectedPackage) return;

      this.isPurchasing = true;
      try {
        await api.purchaseCredits(this.selectedPackage.credits);
        this.user = await api.getUserProfile(); // Refresh user data
        this.showPurchaseModal = false;
        alert(
          `Successfully purchased ${this.selectedPackage.credits} credits!`
        );
      } catch (error) {
        alert(error.message);
      } finally {
        this.isPurchasing = false;
        this.selectedPackage = null;
      }
    },
  },

  async created() {
    try {
      this.user = await api.getUserProfile();
    } catch (error) {
      console.error("Failed to load user profile:", error);
    }
  },

  beforeUnmount() {
    this.stopStatusChecking();
  },
};
</script>

<style scoped>
.service-description {
  color: #666;
  font-size: 0.9rem;
  font-weight: normal;
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
}

.optional-services {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.optional-services h3 {
  color: #2c3e50;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.service-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.service-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.service-option label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.hero {
  background: linear-gradient(135deg, #4a90e2, #50e3c2);
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
  opacity: 0.9;
}

.user-info {
  margin-top: 2rem;
  font-size: 1.1rem;
}

.credits {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.demo-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 2rem;
}

.demo-container h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.demo-container > p {
  color: #666;
  margin-bottom: 2rem;
}

.lead-generation-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
}

.input-with-button {
  display: flex;
  gap: 1rem;
}

textarea,
input {
  flex: 1;
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

textarea {
  min-height: 100px;
  resize: vertical;
}

textarea:focus,
input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.apply-button {
  padding: 0.75rem 1.5rem;
  background-color: #50e3c2;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  align-self: flex-start;
}

.apply-button:hover:not(:disabled) {
  background-color: #3dd1b0;
  transform: translateY(-1px);
}

.apply-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.credit-info {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.credit-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e9ecef;
}

.complexity-info,
.credit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.complexity-low {
  color: #27ae60;
}
.complexity-medium {
  color: #f39c12;
}
.complexity-high {
  color: #e67e22;
}
.complexity-very-high {
  color: #e74c3c;
}

.credit-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.credit-item.total {
  font-weight: 600;
  color: #2c3e50;
  font-size: 1.1rem;
}

.insufficient-credits {
  color: #e74c3c;
  font-weight: 500;
  text-align: right;
}

.cta-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cta-button:hover:not(:disabled) {
  background-color: #357abd;
  transform: translateY(-2px);
}

.cta-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

/* Task Progress Styles */
.task-progress {
  margin-top: 2rem;
}

.status-container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.status-indicator {
  text-align: center;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
  background: #f8f9fa;
}

.status-indicator.pending {
  color: #f39c12;
}
.status-indicator.processing {
  color: #3498db;
}
.status-indicator.completed {
  color: #27ae60;
}
.status-indicator.failed {
  color: #e74c3c;
}

.progress-display {
  margin-bottom: 2rem;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-bar-inner {
  height: 100%;
  background: #4a90e2;
  transition: width 0.3s ease;
}

.progress-bar-inner.partial {
  background: #f39c12;
}

.progress-text {
  text-align: center;
  color: #666;
}

.progress-warning {
  color: #f39c12;
  font-weight: 500;
}

.task-statuses {
  display: grid;
  gap: 1rem;
  margin: 1.5rem 0;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-radius: 6px;
  background: #f8f9fa;
}

.task-status.completed {
  border-left: 4px solid #27ae60;
}
.task-status.processing {
  border-left: 4px solid #3498db;
}
.task-status.pending {
  border-left: 4px solid #f39c12;
}
.task-status.failed {
  border-left: 4px solid #e74c3c;
}

.task-label {
  font-weight: 600;
  color: #2c3e50;
}

.task-status-text {
  color: #666;
}

.task-error-icon {
  margin-left: auto;
  cursor: help;
}

.warning-section,
.error-section {
  margin: 1rem 0;
}

.warning-message {
  padding: 0.75rem;
  background: #fff3cd;
  color: #856404;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.error-message {
  padding: 0.75rem;
  background: #f8d7da;
  color: #721c24;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.download-section {
  text-align: center;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.download-button,
.retry-button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.download-button {
  background-color: #27ae60;
  color: white;
  border: none;
  margin-right: 1rem;
}

.download-button:hover {
  background-color: #219a52;
}

.retry-button {
  background-color: #f39c12;
  color: white;
  border: none;
}

.retry-button:hover {
  background-color: #d68910;
}

/* Credit Purchase Modal Styles */
.purchase-credits-btn {
  margin-left: 1rem;
  padding: 0.5rem 1rem;
  background-color: #50e3c2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.purchase-credits-btn:hover {
  background-color: #3dd1b0;
  transform: translateY(-1px);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background-color: white;
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #2c3e50;
}

.credit-packages {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.credit-package {
  padding: 1.5rem;
  border: 2px solid #eee;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.credit-package:hover {
  border-color: #4a90e2;
  transform: translateY(-2px);
}

.credit-package.selected {
  border-color: #4a90e2;
  background-color: #f8f9ff;
}

.credit-package h3 {
  margin: 0;
  color: #2c3e50;
}

.credit-package .price {
  font-size: 1.5rem;
  font-weight: bold;
  color: #4a90e2;
  margin: 0.5rem 0;
}

.credit-package .savings {
  color: #27ae60;
  font-weight: 600;
  margin: 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.purchase-button,
.cancel-button {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.purchase-button {
  background-color: #4a90e2;
  color: white;
  border: none;
}

.purchase-button:hover:not(:disabled) {
  background-color: #357abd;
}

.purchase-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.cancel-button {
  background-color: #f8f9fa;
  color: #2c3e50;
  border: 1px solid #dee2e6;
}

.cancel-button:hover {
  background-color: #e9ecef;
}

@media (max-width: 768px) {
  .credit-packages {
    grid-template-columns: 1fr;
  }

  .modal {
    margin: 1rem;
    padding: 1.5rem;
  }
}
</style>
