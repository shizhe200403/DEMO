import { defineStore } from "pinia";
import { getMe, login as loginApi } from "../api/auth";

type UserData = Record<string, any> | null;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    accessToken: localStorage.getItem("access_token") || "",
    refreshToken: localStorage.getItem("refresh_token") || "",
    user: null as UserData,
    ready: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },
  actions: {
    setTokens(access: string, refresh: string) {
      this.accessToken = access;
      this.refreshToken = refresh;
      localStorage.setItem("access_token", access);
      localStorage.setItem("refresh_token", refresh);
    },
    clearAuth() {
      this.accessToken = "";
      this.refreshToken = "";
      this.user = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    },
    async login(username: string, password: string) {
      const response = await loginApi(username, password);
      this.setTokens(response.data.access, response.data.refresh);
      await this.fetchMe();
    },
    async fetchMe() {
      if (!this.accessToken) return;
      const response = await getMe();
      this.user = response.data?.data ?? null;
      this.ready = true;
    },
  },
});
