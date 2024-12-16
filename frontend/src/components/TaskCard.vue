<template>
  <div class="task-card" :class="task.status.toLowerCase()">
    <div class="task-info">
      <h4>Lead Generation Task</h4>
      <div class="task-details">
        <p><strong>ICP:</strong> {{ task.icp }}</p>
        <p><strong>Status:</strong> {{ task.status_message }}</p>
        <p>
          <strong>Progress:</strong> {{ task.total_leads_found }} /
          {{ task.total_leads_needed }} leads
        </p>
        <p><strong>Created:</strong> {{ formatDate(task.created_at) }}</p>
        <p v-if="task.get_work_email || task.get_phone_number">
          <strong>Additional Services:</strong>
          <span v-if="task.get_work_email">Work Email</span>
          <span v-if="task.get_work_email && task.get_phone_number">, </span>
          <span v-if="task.get_phone_number">Phone Number</span>
        </p>
      </div>

      <div v-if="showProgress && isActive" class="progress-section">
        <div class="progress-bar">
          <div
            class="progress"
            :style="{ width: progressPercentage + '%' }"
          ></div>
        </div>
        <span class="progress-text">{{ progressPercentage }}%</span>
      </div>

      <div v-if="showDownload && isCompleted" class="actions">
        <button
          class="download-btn"
          @click="$emit('download', task.group_id)"
          :disabled="!task.can_download"
        >
          Download Results
        </button>
      </div>

      <div v-if="task.warnings && task.warnings.length" class="warnings">
        <p
          v-for="(warning, index) in task.warnings"
          :key="index"
          class="warning-text"
        >
          {{ warning }}
        </p>
      </div>

      <div v-if="task.errors && task.errors.length" class="errors">
        <p
          v-for="(error, index) in task.errors"
          :key="index"
          class="error-text"
        >
          {{ error }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "TaskCard",
  props: {
    task: {
      type: Object,
      required: true,
    },
    showProgress: {
      type: Boolean,
      default: false,
    },
    showDownload: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    isActive() {
      return ["pending", "processing"].includes(this.task.status.toLowerCase());
    },
    isCompleted() {
      return this.task.status.toLowerCase() === "completed";
    },
    progressPercentage() {
      if (this.task.total_leads_needed === 0) return 0;
      return Math.round(
        (this.task.total_leads_found / this.task.total_leads_needed) * 100
      );
    },
  },
  methods: {
    formatDate(dateString) {
      return new Date(dateString).toLocaleString();
    },
  },
};
</script>

<style scoped>
.task-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.task-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.task-card.completed {
  border-left: 4px solid #4caf50;
}

.task-card.processing {
  border-left: 4px solid #2196f3;
}

.task-card.pending {
  border-left: 4px solid #ff9800;
}

.task-card.failed {
  border-left: 4px solid #f44336;
}

h4 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.task-details {
  margin-bottom: 15px;
}

.task-details p {
  margin: 8px 0;
  color: #34495e;
}

.progress-section {
  margin: 15px 0;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #2196f3;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.9em;
  color: #666;
  margin-top: 5px;
  display: inline-block;
}

.actions {
  margin-top: 15px;
}

.download-btn {
  background: #4caf50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.download-btn:hover {
  background: #45a049;
}

.download-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.warnings {
  margin-top: 15px;
  padding: 10px;
  background: #fff3e0;
  border-radius: 4px;
}

.warning-text {
  color: #f57c00;
  margin: 5px 0;
  font-size: 0.9em;
}

.errors {
  margin-top: 15px;
  padding: 10px;
  background: #ffebee;
  border-radius: 4px;
}

.error-text {
  color: #d32f2f;
  margin: 5px 0;
  font-size: 0.9em;
}

@media (max-width: 768px) {
  .task-card {
    padding: 15px;
  }
}
</style>
