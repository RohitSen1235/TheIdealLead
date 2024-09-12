import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import FeaturesView from "../views/FeaturesView.vue";
import DemoView from "../views/DemoView.vue"; // Import the Demo view
// import PricingView from "../views/PricingView.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/features",
    name: "features",
    component: FeaturesView,
  },
  {
    path: "/demo", // Add the route for the Demo page
    name: "demo",
    component: DemoView,
  },
  // {
  //   path: "/pricing",
  //   name: "pricing",
  //   component: PricingView,
  // },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
