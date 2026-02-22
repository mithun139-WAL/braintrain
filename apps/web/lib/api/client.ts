import axios from "axios";

// Core HTTP Engine
export const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001",
    withCredentials: true, // Essential for httpOnly cookies
});

// Centralized error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        // Optional: Global unauthenticated redirect handling
        // if (error.response?.status === 401 && typeof window !== 'undefined') {
        //   window.location.href = '/login';
        // }

        // Normalize error format for the hooks layer
        return Promise.reject(
            error.response?.data?.message || "An unexpected error occurred."
        );
    }
);
