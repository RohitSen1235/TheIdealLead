<template>
  <div class="lead-form-container">
    <form @submit.prevent="submitLead" class="lead-form">
      <h2>Get Early Access</h2>
      <p>
        The.Ideal.Leads platform is currently in development. Sign up to get
        early access when it's ready. This is a limited time offer.
      </p>
      <div class="form-group">
        <label for="name">Name</label>
        <input
          v-model="name"
          type="text"
          id="name"
          placeholder="John Doe"
          required
        />
      </div>
      <div class="form-group">
        <label for="email">Email</label>
        <input
          v-model="email"
          type="email"
          id="email"
          placeholder="john@example.com"
          required
        />
      </div>
      <div class="form-group">
        <label for="company">Company</label>
        <input
          v-model="company"
          type="text"
          id="company"
          placeholder="Acme Inc."
          required
        />
      </div>
      <div class="form-group">
        <label for="phone">Phone Number</label>
        <input
          v-model="phone"
          type="tel"
          id="phone"
          placeholder="+1 (555) 123-4567"
          required
        />
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
      <button type="submit" class="cta-button" :disabled="isSubmitting">
        {{ isSubmitting ? "Submitting..." : "Sign Up" }}
      </button>
    </form>
  </div>
</template>

<script>
import api from "@/services/api";

export default {
  name: "LeadForm",
  data() {
    return {
      name: "",
      email: "",
      company: "",
      phone: "",
      isSubmitting: false,
      errorMessage: "",
      successMessage: "",
    };
  },
  methods: {
    async submitLead() {
      this.isSubmitting = true;
      this.errorMessage = "";
      this.successMessage = "";

      try {
        const response = await api.submitLead({
          name: this.name,
          email: this.email,
          company: this.company,
          phone: this.phone,
        });

        // Reset form fields
        this.name = "";
        this.email = "";
        this.company = "";
        this.phone = "";

        // Show success message
        this.successMessage =
          response.message ||
          "Thank you for your interest! We will be in touch soon.";
      } catch (error) {
        console.error("Error submitting lead:", error);
        this.errorMessage =
          error.message ||
          "There was an error submitting your information. Please try again.";
      } finally {
        this.isSubmitting = false;
      }
    },
  },
};
</script>

<style scoped>
.lead-form-container {
  max-width: 500px;
  margin: 0 auto;
  padding: 2rem;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.lead-form {
  display: flex;
  flex-direction: column;
}

.lead-form p {
  margin-bottom: 2rem;
  text-align: center;
  font-size: 0.9rem;
  font-style: italic;
  color: #203fca;
}

h2 {
  color: #2c3e50;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
  position: relative;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #34495e;
  font-weight: bold;
  font-size: 0.9rem;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.8);
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.3);
}

.error-message {
  color: #e74c3c;
  background-color: #fde8e7;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 0.9rem;
}

.success-message {
  color: #27ae60;
  background-color: #e8f5e9;
  padding: 0.75rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 0.9rem;
}

.cta-button {
  background-color: #3498db;
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
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.cta-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

@media (max-width: 768px) {
  .lead-form-container {
    padding: 1.5rem;
  }
}
</style>
