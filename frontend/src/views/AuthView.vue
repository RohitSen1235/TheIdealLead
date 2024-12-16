<template>
  <div>
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <h1>Welcome to TargetSphere</h1>
        <p>
          Join our platform to unlock the power of AI-powered lead generation
        </p>
      </div>
    </section>

    <!-- Auth Form -->
    <div class="auth-container">
      <div class="auth-tabs">
        <button :class="{ active: !isLogin }" @click="isLogin = false">
          Register
        </button>
        <button :class="{ active: isLogin }" @click="isLogin = true">
          Login
        </button>
      </div>

      <!-- Registration Form -->
      <form v-if="!isLogin" @submit.prevent="handleRegister" class="auth-form">
        <h2>Create Your Account</h2>
        <p class="subtitle">Get started with 100 free credits!</p>

        <div class="form-group">
          <label for="name">Full Name</label>
          <input
            v-model="registerForm.name"
            type="text"
            id="name"
            required
            placeholder="Enter your full name"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            v-model="registerForm.email"
            type="email"
            id="email"
            required
            placeholder="Enter your email"
          />
        </div>

        <div class="form-group">
          <label for="company">Company</label>
          <input
            v-model="registerForm.company"
            type="text"
            id="company"
            required
            placeholder="Enter your company name"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            v-model="registerForm.password"
            type="password"
            id="password"
            required
            placeholder="Create a password"
          />
        </div>

        <button type="submit" class="auth-button" :disabled="isSubmitting">
          {{ isSubmitting ? "Creating Account..." : "Create Account" }}
        </button>
      </form>

      <!-- Login Form -->
      <form v-else @submit.prevent="handleLogin" class="auth-form">
        <h2>Welcome Back</h2>
        <p class="subtitle">Login to your account</p>

        <div class="form-group">
          <label for="loginEmail">Email</label>
          <input
            v-model="loginForm.email"
            type="email"
            id="loginEmail"
            required
            placeholder="Enter your email"
          />
        </div>

        <div class="form-group">
          <label for="loginPassword">Password</label>
          <input
            v-model="loginForm.password"
            type="password"
            id="loginPassword"
            required
            placeholder="Enter your password"
          />
        </div>

        <button type="submit" class="auth-button" :disabled="isSubmitting">
          {{ isSubmitting ? "Logging in..." : "Login" }}
        </button>
      </form>

      <!-- Error Display -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import api from "@/services/api";

export default {
  data() {
    return {
      isLogin: true, // Set default to login view
      isSubmitting: false,
      error: null,
      registerForm: {
        name: "",
        email: "",
        company: "",
        password: "",
      },
      loginForm: {
        email: "",
        password: "",
      },
    };
  },

  methods: {
    async handleRegister() {
      this.isSubmitting = true;
      this.error = null;

      try {
        await api.register(this.registerForm);
        this.$router.push("/demo");
      } catch (error) {
        this.error = error.message;
      } finally {
        this.isSubmitting = false;
      }
    },

    async handleLogin() {
      this.isSubmitting = true;
      this.error = null;

      try {
        await api.login(this.loginForm.email, this.loginForm.password);
        this.$router.push("/demo");
      } catch (error) {
        this.error = error.message;
      } finally {
        this.isSubmitting = false;
      }
    },
  },
};
</script>

<style scoped>
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

.auth-container {
  max-width: 500px;
  margin: 2rem auto;
  padding: 2rem;
  background: white;
  border-radius: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.auth-tabs {
  display: flex;
  margin-bottom: 2rem;
  border-bottom: 2px solid #eee;
}

.auth-tabs button {
  flex: 1;
  padding: 1rem;
  font-size: 1.1rem;
  background: none;
  border: none;
  cursor: pointer;
  color: #666;
  transition: all 0.3s ease;
}

.auth-tabs button.active {
  color: #4a90e2;
  border-bottom: 2px solid #4a90e2;
  margin-bottom: -2px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-weight: 600;
  color: #34495e;
}

input {
  padding: 0.75rem;
  border: 2px solid #eee;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
}

.auth-button {
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 1rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.auth-button:hover {
  background-color: #357abd;
  transform: translateY(-2px);
}

.auth-button:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.error-message {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fde8e7;
  color: #e74c3c;
  border-radius: 8px;
  text-align: center;
}

@media (max-width: 768px) {
  .auth-container {
    margin: 1rem;
    padding: 1.5rem;
  }
}
</style>
