import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import AuthView from "../views/AuthView.vue";

const routes = [
  {
    path: "/",
    name: "home",
    component: HomeView,
  },
  {
    path: "/auth",
    name: "auth",
    component: AuthView,
    meta: { requiresGuest: true },
  },
  {
    path: "/about",
    name: "about",
    component: () => import("../views/AboutView.vue"),
  },
  {
    path: "/features",
    name: "features",
    component: () => import("../views/FeaturesView.vue"),
  },
  {
    path: "/pricing",
    name: "pricing",
    component: () => import("../views/PricingView.vue"),
  },
  {
    path: "/demo",
    name: "demo",
    component: () => import("../views/DemoView.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/tasks",
    name: "tasks",
    component: () => import("../views/TaskHistoryView.vue"),
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

// Navigation guard
router.beforeEach((to, from, next) => {
  const hasToken = !!localStorage.getItem("access_token");

  // Routes that require authentication
  if (to.matched.some((record) => record.meta.requiresAuth)) {
    if (!hasToken) {
      next({ name: "auth" });
      return;
    }
  }

  // Routes that require guest (non-authenticated) access
  if (to.matched.some((record) => record.meta.requiresGuest)) {
    if (hasToken) {
      next({ name: "demo" });
      return;
    }
  }

  next();
});

export default router;
