import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import FeaturesView from "../views/FeaturesView.vue";
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
