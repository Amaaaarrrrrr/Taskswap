// src/hooks/useAuth.ts
import { useAuthContext } from "../context/AuthContext";
import * as authService from "../services/authService";

export const useAuth = () => {
  const { user, token, login, logout } = useAuthContext();

  const handleLogin = async (email: string, password: string) => {
    const data = await authService.login(email, password);
    login(data.user, data.token);
  };

  const handleRegister = async (name: string, email: string, password: string) => {
    const data = await authService.register(name, email, password);
    login(data.user, data.token); // auto-login after register
  };

  const handleLogout = () => {
    authService.logout();
    logout();
  };

  return { user, token, handleLogin, handleRegister, handleLogout };
};
