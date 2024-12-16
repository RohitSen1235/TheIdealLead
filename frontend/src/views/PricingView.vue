<template>
  <div class="pricing-page">
    <section class="hero">
      <div class="container">
        <div class="hero-content">
          <h1>{{ title }}</h1>
          <p>{{ subtitle }}</p>
          <button @click="ctaAction" class="cta-button">Get Started</button>
        </div>
      </div>
    </section>

    <section class="pricing">
      <div class="container">
        <h2>Choose Your Credit Package</h2>
        <div class="pricing-plans">
          <div
            class="plan"
            v-for="(plan, index) in plans"
            :key="index"
            :class="{ featured: plan.featured }"
          >
            <div class="plan-content">
              <h3>{{ plan.name }}</h3>
              <p class="price">${{ plan.price }}</p>
              <p class="credits">{{ plan.credits }} Credits</p>
              <ul>
                <li
                  v-for="(feature, featureIndex) in plan.features"
                  :key="featureIndex"
                >
                  {{ feature }}
                </li>
              </ul>
            </div>
            <button @click="purchaseCredits(plan)" class="plan-cta">
              Get Credits
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import api from "@/services/api";

export default {
  name: "PricingView",
  data() {
    return {
      title: "Get More Credits",
      subtitle: "Choose the credit package that fits your needs",
      plans: [
        {
          name: "Starter",
          price: 49,
          credits: 500,
          features: [
            "Generate up to 500 leads",
            "Basic support",
            "Credits never expire",
          ],
        },
        {
          name: "Pro",
          price: 99,
          credits: 1100,
          features: [
            "Generate up to 1,100 leads",
            "Priority support",
            "Credits never expire",
            "10% bonus credits",
          ],
          featured: true,
        },
        {
          name: "Enterprise",
          price: 199,
          credits: 2500,
          features: [
            "Generate up to 2,500 leads",
            "24/7 dedicated support",
            "Credits never expire",
            "25% bonus credits",
            "Custom lead criteria",
          ],
        },
      ],
    };
  },
  methods: {
    ctaAction() {
      const element = document.querySelector(".pricing");
      element.scrollIntoView({ behavior: "smooth" });
    },
    async purchaseCredits(plan) {
      if (!this.$store.state.user) {
        // Redirect to login if not authenticated
        this.$router.push("/auth");
        return;
      }

      try {
        await api.purchaseCredits(plan.credits);
        // Refresh user data to get updated credits
        await this.$store.dispatch("updateUserProfile");
        this.$notify({
          type: "success",
          text: `Successfully added ${plan.credits} credits!`,
        });
      } catch (error) {
        this.$notify({
          type: "error",
          text: error.message || "Failed to add credits",
        });
      }
    },
  },
};
</script>

<style scoped>
.hero {
  background: linear-gradient(135deg, #4a90e2, #50e3c2);
  color: white;
  min-height: 300px;
  display: flex;
  align-items: center;
  padding: 4rem 0;
  text-align: center;
}

.hero-content {
  width: 100%;
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

.pricing {
  padding: 4rem 0;
  background-color: #f8f9fa;
}

.pricing h2 {
  text-align: center;
  margin-bottom: 3rem;
  font-size: 2.5rem;
  color: #4a90e2;
}

.pricing-plans {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.plan {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  width: 300px;
  text-align: center;
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.plan-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.plan:hover {
  transform: translateY(-5px);
}

.plan.featured {
  border: 2px solid #4a90e2;
  transform: scale(1.05);
}

.plan h3 {
  font-size: 1.5rem;
  color: #4a90e2;
  margin-bottom: 1rem;
}

.plan .price {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.plan .credits {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 1.5rem;
}

.plan ul {
  list-style-type: none;
  padding: 0;
  margin-bottom: 1.5rem;
  flex-grow: 1;
}

.plan li {
  margin-bottom: 0.5rem;
}

.plan-cta {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-top: 1rem;
}

.plan-cta:hover {
  background-color: #3a7bc8;
}

@media (max-width: 768px) {
  .pricing-plans {
    flex-direction: column;
    align-items: center;
  }

  .plan {
    width: 100%;
    max-width: 300px;
  }

  .plan.featured {
    transform: none;
  }
}
</style>
