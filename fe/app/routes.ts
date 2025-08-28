import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("/dashboard", "routes/dashboard.tsx"),
  route("/banking", "routes/banking.tsx"),
  route("/login", "routes/login.tsx"),
  route("/register", "routes/register.tsx"),
  route("/trading", "routes/trading.tsx"),
] satisfies RouteConfig;
