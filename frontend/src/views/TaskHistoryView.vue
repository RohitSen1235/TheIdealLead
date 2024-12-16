<template>
  <div class="task-history">
    <h2>Lead Generation History</h2>

    <!-- Active Tasks Section -->
    <div v-if="activeTasks.length" class="active-tasks">
      <h3>Active Tasks</h3>
      <div v-for="task in activeTasks" :key="task.group_id" class="task-list">
        <TaskCard :task="task" :showProgress="true" @refresh="refreshTasks" />
      </div>
    </div>

    <!-- Completed Tasks Section -->
    <div class="completed-tasks">
      <h3>Completed Tasks</h3>
      <div v-if="completedTasks.length" class="task-list">
        <div v-for="task in completedTasks" :key="task.group_id">
          <TaskCard
            :task="task"
            :showDownload="true"
            @download="downloadResults"
          />
        </div>
      </div>
      <div v-else class="no-tasks">
        <p>No completed tasks yet</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";
import TaskCard from "@/components/TaskCard.vue";

export default {
  name: "TaskHistoryView",
  components: {
    TaskCard,
  },
  data() {
    return {
      tasks: [],
      pollingInterval: null,
    };
  },
  computed: {
    activeTasks() {
      return this.tasks
        .filter(
          (task) => task.status === "pending" || task.status === "processing"
        )
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    },
    completedTasks() {
      return this.tasks
        .filter(
          (task) => task.status === "completed" || task.status === "failed"
        )
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    },
  },
  methods: {
    async fetchTasks() {
      try {
        const response = await api.getUserTasks();
        this.tasks = response;
      } catch (error) {
        console.error("Failed to fetch tasks:", error);
      }
    },
    async downloadResults(groupId) {
      try {
        await api.downloadResults(groupId);
      } catch (error) {
        console.error("Failed to download results:", error);
      }
    },
    startPolling() {
      this.pollingInterval = setInterval(async () => {
        if (this.activeTasks.length > 0) {
          await this.fetchTasks();
        } else {
          this.stopPolling();
        }
      }, 5000); // Poll every 5 seconds
    },
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
      }
    },
    async refreshTasks() {
      await this.fetchTasks();
      if (this.activeTasks.length > 0 && !this.pollingInterval) {
        this.startPolling();
      }
    },
  },
  async created() {
    await this.refreshTasks();
  },
  beforeUnmount() {
    this.stopPolling();
  },
};
</script>

<style scoped>
.task-history {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 30px;
}

h3 {
  color: #34495e;
  margin: 20px 0;
}

.task-list {
  display: grid;
  gap: 20px;
  margin-bottom: 30px;
}

.no-tasks {
  text-align: center;
  color: #666;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .task-history {
    padding: 10px;
  }
}
</style>
