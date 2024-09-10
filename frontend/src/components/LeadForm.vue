<template>
  <form @submit.prevent="submitLead" class="lead-form">
    <div class="form-group">
      <input v-model="name" type="text" placeholder="Name" required />
    </div>
    <div class="form-group">
      <input v-model="email" type="email" placeholder="Email" required />
    </div>
    <div class="form-group">
      <input v-model="company" type="text" placeholder="Company" required />
    </div>
    <div class="form-group">
      <input v-model="phone" type="tel" placeholder="Phone Number" required />
    </div>
    <button type="submit" class="cta-button" :disabled="isSubmitting">
      {{ isSubmitting ? "Submitting..." : "Get Started" }}
    </button>
  </form>
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
    };
  },
  methods: {
    async submitLead() {
      this.isSubmitting = true;
      try {
        const response = await api.submitLead({
          name: this.name,
          email: this.email,
          company: this.company,
          phone: this.phone,
        });
        console.log("Lead submitted successfully:", response);
        // Reset form fields
        this.name = "";
        this.email = "";
        this.company = "";
        this.phone = "";
        // Show success message to the user
        alert("Thank you for your interest! We will be in touch soon.");
      } catch (error) {
        console.error("Error submitting lead:", error);
        // Show error message to the user
        alert(
          "There was an error submitting your information. Please try again."
        );
      } finally {
        this.isSubmitting = false;
      }
    },
  },
};
</script>

<style scoped>
.lead-form {
  max-width: 400px;
  margin: 0 auto;
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.form-group {
  margin-bottom: 1rem;
}

input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #4a90e2;
}

.cta-button {
  width: 100%;
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.cta-button:hover {
  background-color: #3a7bc8;
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .lead-form {
    padding: 1.5rem;
  }
}
</style>
