<template>
  <section class="hero">
    <div class="container">
      <div class="hero-content">
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
        <button @click="ctaAction" class="cta-button">Get Access</button>
      </div>
    </div>
  </section>

  <section class="feature-details">
    <div class="container">
      <div class="feature-item">
        <div class="feature-header">
          <i class="fas fa-user-circle"></i>
          <h2>Customer Persona-based Lead Generation</h2>
        </div>
        <p>
          Our advanced AI algorithms analyze vast amounts of data to create
          detailed customer personas. This allows us to generate highly targeted
          leads that match your ideal customer profile, increasing your
          conversion rates and ROI.
        </p>
        <ul>
          <li>Create multiple customer personas</li>
          <li>AI-driven data analysis</li>
          <li>Continuously improving accuracy</li>
        </ul>
      </div>

      <div class="feature-item">
        <div class="feature-header">
          <i class="fas fa-envelope"></i>
          <h2>Validated Email Addresses</h2>
        </div>
        <p>
          Say goodbye to bounced emails and wasted efforts. Our system
          rigorously verifies each email address to ensure accuracy and
          deliverability, saving you time and improving your email marketing
          effectiveness.
        </p>
        <ul>
          <li>Real-time email verification</li>
          <li>Reduce bounce rates</li>
          <li>Improve sender reputation</li>
        </ul>
      </div>

      <div class="feature-item">
        <div class="feature-header">
          <i class="fas fa-share-alt"></i>
          <h2>Social Media Profiles</h2>
        </div>
        <p>
          Get a 360-degree view of your leads with comprehensive social media
          profiles. Understand their interests, behaviors, and preferences to
          tailor your outreach and create more meaningful connections.
        </p>
        <ul>
          <li>Aggregate data from multiple platforms</li>
          <li>Gain insights into lead behavior</li>
          <li>Personalize your marketing approach</li>
        </ul>
      </div>

      <div class="feature-item">
        <div class="feature-header">
          <i class="fas fa-chart-line"></i>
          <h2>Real-time Analytics</h2>
        </div>
        <p>
          Stay on top of your lead generation efforts with our powerful,
          real-time analytics dashboard. Monitor performance, identify trends,
          and make data-driven decisions to optimize your campaigns.
        </p>
        <ul>
          <li>Customizable dashboards</li>
          <li>Key performance indicators</li>
          <li>Export and share reports</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script>
import "@/assets/styles/features.css";

export default {
  name: "FeaturesView",
  data() {
    return {
      title: "Our Features",
      subtitle:
        "Discover how LeadGen Pro can revolutionize your lead generation process",
    };
  },
  methods: {
    ctaAction() {
      this.goToHomeForm();
    },
    goToHomeForm() {
      this.$router.push({ path: "/", query: { scrollTo: "lead-form" } });
    },
  },
};
</script>
<!-- 
<style scoped>
.hero {
  background: linear-gradient(135deg, #4a90e2, #50e3c2);
  color: white;
  padding: 4rem 0;
  text-align: center;
  display: flex;
  align-items: center;
  min-height: 300px;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero h1 {
  font-size: 3rem;
  margin-bottom: 1rem;
  line-height: 1.2;
}

.hero p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-button {
  background-color: white;
  color: #4a90e2;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.cta-button:hover {
  background-color: #f0f0f0;
  transform: translateY(-2px);
}

.feature-details {
  padding: 4rem 0;
}


</style> -->
