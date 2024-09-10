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
        <h2>Choose Your Plan</h2>
        <div class="billing-toggle">
          <span :class="{ active: !isAnnual }">Monthly</span>
          <label class="switch">
            <input type="checkbox" v-model="isAnnual" />
            <span class="slider"></span>
          </label>
          <span :class="{ active: isAnnual }">Annual</span>
        </div>
        <div class="pricing-plans">
          <div
            class="plan"
            v-for="(plan, index) in plans"
            :key="index"
            :class="{ featured: plan.featured }"
          >
            <div class="plan-content">
              <h3>{{ plan.name }}</h3>
              <p class="price">
                {{ isAnnual ? plan.annualPrice : plan.monthlyPrice }}
              </p>
              <p class="billing-period">
                {{ isAnnual ? "per year" : "per month" }}
              </p>
              <ul>
                <li
                  v-for="(feature, featureIndex) in plan.features"
                  :key="featureIndex"
                >
                  {{ feature }}
                </li>
              </ul>
            </div>
            <button class="plan-cta">Select Plan</button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: "PricingView",
  data() {
    return {
      title: "Simple, Transparent Pricing",
      subtitle: "Choose the plan that fits your business needs",
      isAnnual: false,
      plans: [
        {
          name: "Starter",
          monthlyPrice: "$49/mo",
          annualPrice: "$530/yr",
          features: ["Up to 1,000 leads", "Basic analytics", "Email support"],
        },
        {
          name: "Pro",
          monthlyPrice: "$99/mo",
          annualPrice: "$1,010/yr",
          features: [
            "Up to 10,000 leads",
            "Advanced analytics",
            "Priority support",
            "API access",
          ],
          featured: true,
        },
        {
          name: "Enterprise",
          monthlyPrice: "$199/mo",
          annualPrice: "$1,910/yr",
          features: [
            "Unlimited leads",
            "Custom analytics",
            "24/7 dedicated support",
            "Full API access",
            "Custom integrations",
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

.billing-toggle {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 2rem;
}

.billing-toggle span {
  margin: 0 3rem;
  color: #666;
  font-size: 2rem;
  transition: color 0.3s ease;
}

.billing-toggle span.active {
  color: #4a90e2;
  font-weight: bold;
}

.switch {
  position: relative;
  display: inline-block;
  width: 160px;
  height: 34px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.4s;
  border-radius: 34px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 26px;
  width: 26px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: 0.4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #4a90e2;
}

input:checked + .slider:before {
  transform: translateX(26px);
}

@media (max-width: 768px) {
  .billing-toggle {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .billing-toggle span {
    margin: 0.5rem;
    font-size: 0.9rem;
  }

  .switch {
    width: 50px;
    height: 28px;
  }

  .slider:before {
    height: 20px;
    width: 20px;
  }

  input:checked + .slider:before {
    transform: translateX(22px);
  }
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

.billing-period {
  font-size: 0.9rem;
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

  .billing-toggle {
    flex-direction: row;
    align-items: center;
    justify-content: center;
  }

  .billing-toggle span {
    margin: 0.5rem;
    font-size: 0.8rem;
  }

  .switch {
    margin: 0.5rem;
  }
}
</style>
