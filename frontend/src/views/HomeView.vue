<template>
  <div class="home">
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
          <button @click="ctaAction" class="cta-button">Get Access</button>
        </div>
      </div>
    </section>

    <section class="features">
      <div class="container">
        <h2>Why Choose The.Ideal.Leads ?</h2>
        <div class="feature-grid">
          <div class="feature-item">
            <i class="fas fa-user-circle"></i>
            <h3>Customer Persona-based Lead Generation</h3>
            <p>
              Generate highly targeted leads using customized customer personas.
            </p>
          </div>
          <div class="feature-item">
            <i class="fas fa-envelope"></i>
            <h3>Validated Email Addresses</h3>
            <p>Ensure your leads have accurate and verified email addresses.</p>
          </div>
          <div class="feature-item">
            <i class="fas fa-share-alt"></i>
            <h3>Social Media Profiles</h3>
            <p>Access comprehensive social media profiles for each lead.</p>
          </div>
          <div class="feature-item">
            <i class="fas fa-chart-line"></i>
            <h3>Real-time Analytics</h3>
            <p>
              Track your lead generation performance with our intuitive
              dashboard.
            </p>
          </div>
        </div>
      </div>
    </section>

    <section id="lead-form-section" class="lead-form-section">
      <div class="container">
        <LeadForm />
      </div>
    </section>
  </div>
</template>

<script>
import LeadForm from "@/components/LeadForm.vue";
import "@/assets/styles/global.css";
export default {
  name: "HomeView",
  data() {
    return {
      title: "Experience AI-powered Lead Generation",
      subtitle:
        "Unlock the potential of your business with cutting-edge technology",
    };
  },
  components: {
    LeadForm,
  },
  methods: {
    ctaAction() {
      this.scrollToLeadForm();
    },
    scrollToLeadForm() {
      const element = document.getElementById("lead-form-section");
      element.scrollIntoView({ behavior: "smooth" });
    },
  },
  mounted() {
    if (this.$route.query.scrollTo === "lead-form") {
      this.$nextTick(() => {
        this.scrollToLeadForm();
      });
    }
  },
};
</script>

<style scoped>
.features {
  padding: 4rem 0;
  background-color: white;
}

.features h2 {
  text-align: center;
  margin-bottom: 3rem;
  font-size: 2.5rem;
  color: #4a90e2;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.feature-item {
  background-color: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.3s ease;
}

.feature-item:hover {
  transform: translateY(-5px);
}

.feature-item i {
  font-size: 2.5rem;
  color: #4a90e2;
  margin-bottom: 1rem;
}

.feature-item h3 {
  margin-bottom: 1rem;
  color: #4a90e2;
  font-size: 1.2rem;
}

.feature-item p {
  font-size: 0.9rem;
  line-height: 1.4;
}

.lead-form-section {
  background-color: #f8f9fa;
  padding: 4rem 0;
}

.lead-form-section h2 {
  text-align: center;
  margin-bottom: 2rem;
  font-size: 2.5rem;
  color: #4a90e2;
}

@media (max-width: 768px) {
  .hero h1 {
    font-size: 2.5rem;
  }

  .hero p {
    font-size: 1rem;
  }
}
</style>
