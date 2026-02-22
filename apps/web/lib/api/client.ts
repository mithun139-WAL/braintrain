import axios from "axios";
import { useAuthStore } from "@/lib/store/auth.store";

// Core HTTP Engine
export const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001",
    withCredentials: true, // Essential for httpOnly cookies
});

// Request Interceptor: Attach Auth Token
apiClient.interceptors.request.use(
    (config) => {
        const token = useAuthStore.getState().token;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Centralized error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // Optional: Global unauthenticated redirect handling
        // if (error.response?.status === 401 && typeof window !== 'undefined') {
        //   window.location.href = '/login';
        // }

        // Normalize error format for the hooks layer
        const message = error.response?.data?.message;
        const normalizedMessage = Array.isArray(message)
            ? message.join(". ")
            : message || "An unexpected error occurred.";

        return Promise.reject(normalizedMessage);
    }
);
