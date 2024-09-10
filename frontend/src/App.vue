<template>
  <div id="app">
    <header>
      <div class="container">
        <h1>LeadGen Pro</h1>
        <nav>
          <router-link to="/">Home</router-link>
          <router-link to="/features">Features</router-link>
          <router-link to="/pricing">Pricing</router-link>
          <router-link to="/contact">Contact</router-link>
        </nav>
      </div>
    </header>

    <router-view></router-view>

    <footer>
      <div class="container">
        <p>&copy; 2023 LeadGen Pro. All rights reserved.</p>
        <div class="social-links">
          <a href="#" aria-label="Facebook"><i class="fab fa-facebook"></i></a>
          <a href="#" aria-label="Twitter"><i class="fab fa-twitter"></i></a>
          <a href="#" aria-label="LinkedIn"><i class="fab fa-linkedin"></i></a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: "App",
};
</script>

<style>
@import url("https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap");
@import url("https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css");

:root {
  --primary-color: #4a90e2;
  --secondary-color: #50e3c2;
  --text-color: #333;
  --bg-color: #f8f9fa;
}

body {
  font-family: "Poppins", sans-serif;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  color: var(--text-color);
  background-color: var(--bg-color);
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

header {
  background-color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: fixed;
  width: 100%;
  z-index: 1000;
}

header .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
}

header h1 {
  margin: 0;
  font-size: 1.5rem;
  color: var(--primary-color);
}

nav a {
  color: var(--text-color);
  text-decoration: none;
  margin-left: 20px;
  font-weight: 600;
  transition: color 0.3s ease;
}

nav a:hover {
  color: var(--primary-color);
}

footer {
  background-color: white;
  color: var(--text-color);
  padding: 2rem 0;
  margin-top: 2rem;
  box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
}

footer .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.social-links a {
  color: var(--text-color);
  font-size: 1.2rem;
  margin-left: 15px;
  transition: color 0.3s ease;
}

.social-links a:hover {
  color: var(--primary-color);
}

button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 50px;
  cursor: pointer;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

button:hover {
  background-color: var(--secondary-color);
  transform: translateY(-2px);
}
</style>
