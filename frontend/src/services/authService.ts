// src/services/authService.ts
import axios from "axios";

const API_URL = "http://localhost:5000/api/auth"; // adjust if needed

export const register = async (name: string, email: string, password: string) => {
  const res = await axios.post(`${API_URL}/register`, { name, email, password });
  return res.data; // contains { user, token }
};

export const login = async (email: string, password: string) => {
  const res = await axios.post(`${API_URL}/login`, { email, password });
  return res.data; // contains { user, token }
};

export const logout = async () => {
  // optional: call API to blacklist token if you’re doing JWT invalidation
  localStorage.removeItem("user");
  localStorage.removeItem("token");
};
