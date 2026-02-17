import axios from "axios";

export const api = axios.create({
    baseURL: "/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem("token");
    console.log("API Request:", config.url, "Token exists:", !!token);
    if (token && config.headers) {
        config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
});
