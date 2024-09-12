<template>
  <div>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Experiance the power of AI-powered lead generation</h1>
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
        <span style="color: #4a90e2; font-weight: bold"
          >Note: This is a demo version, so there are restictions for
          usage.</span
        >
      </p>
      <form @submit.prevent="startLeadGeneration" class="lead-generation-form">
        <div class="form-group">
          <label for="icp">Ideal Customer Profile</label>
          <textarea
            v-model="icp"
            id="icp"
            placeholder="Describe your ideal customer..."
            required
          ></textarea>
        </div>
        <div class="form-group">
          <label for="numberOfLeads">Number of Leads</label>
          <input
            v-model="numberOfLeads"
            type="number"
            id="numberOfLeads"
            placeholder="Expected number of leads"
            required
          />
        </div>
        <button type="submit" class="cta-button">Start Lead Generation</button>
      </form>
      <p v-if="message" class="response-message">{{ message }}</p>
    </div>
  </div>
</template>

<script>
import api from "@/services/api"; // Adjust the import path as necessary
import "@/assets/styles/global.css";
export default {
  data() {
    return {
      icp: "",
      numberOfLeads: null,
      message: "",
    };
  },
  methods: {
    async startLeadGeneration() {
      try {
        const response = await api.startLeadGeneration({
          ideal_customer_profile: this.icp,
          number_of_leads: this.numberOfLeads,
        });
        this.message = response.message;
      } catch (error) {
        this.message =
          "An error occurred while starting the lead generation process.";
        console.error(error);
      }
    },
  },
};
</script>

<style scoped>
/* Hero Section Styles */
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

/* Demo Container Styles */
.demo-container {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  color: #333;
}

h2 {
  text-align: center;
  margin-bottom: 1rem;
  font-size: 2rem;
}

p {
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.lead-generation-form {
  display: flex;
  flex-direction: column;
  /* align-items: center; */
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

textarea,
input {
  width: 100%;
  padding: 0.75rem; /* Adjust padding for equal spacing */
  border: 2px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-sizing: border-box; /* Ensure padding is included in width */
}

textarea:focus,
input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.3);
}

.cta-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 1rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.cta-button:hover {
  background-color: #2980b9;
}

.response-message {
  text-align: center;
  margin-top: 1rem;
  font-size: 1rem;
  color: #f39c12; /* Change color for visibility */
}
</style>
