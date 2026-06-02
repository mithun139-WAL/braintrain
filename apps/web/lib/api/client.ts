import axios from "axios";
import { useAuthStore } from "@/lib/store/auth.store";

// ─── Case Conversion Utilities ────────────────────────────────────────────────
// FastAPI returns snake_case; the frontend uses camelCase.
// These interceptors handle the conversion transparently.

function camelizeKeys(obj: unknown): unknown {
    if (Array.isArray(obj)) {
        return obj.map(camelizeKeys);
    }
    if (obj !== null && typeof obj === "object") {
        return Object.keys(obj as Record<string, unknown>).reduce(
            (acc: Record<string, unknown>, key: string) => {
                const camelKey = key.replace(/_([a-z])/g, (_, letter: string) =>
                    letter.toUpperCase()
                );
                acc[camelKey] = camelizeKeys((obj as Record<string, unknown>)[key]);
                return acc;
            },
            {}
        );
    }
    return obj;
}

function decamelizeKeys(obj: unknown): unknown {
    if (Array.isArray(obj)) {
        return obj.map(decamelizeKeys);
    }
    if (obj !== null && typeof obj === "object") {
        return Object.keys(obj as Record<string, unknown>).reduce(
            (acc: Record<string, unknown>, key: string) => {
                const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
                acc[snakeKey] = decamelizeKeys((obj as Record<string, unknown>)[key]);
                return acc;
            },
            {}
        );
    }
    return obj;
}

// ─── Core HTTP Engine ─────────────────────────────────────────────────────────

export const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL,
    withCredentials: true,
});

// ─── Request Interceptor ──────────────────────────────────────────────────────
// 1. Attach JWT Bearer token from auth store
// 2. Convert camelCase request body → snake_case for FastAPI

apiClient.interceptors.request.use(
    (config) => {
        // Attach auth token
        const token = useAuthStore.getState().token;
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        // Convert request body: camelCase → snake_case
        if (config.data && typeof config.data === "object" && !(config.data instanceof FormData)) {
            config.data = decamelizeKeys(config.data);
        }

        // Convert query params: camelCase → snake_case
        if (config.params && typeof config.params === "object") {
            config.params = decamelizeKeys(config.params);
        }

        return config;
    },
    (error) => Promise.reject(error)
);

// ─── Response Interceptor ─────────────────────────────────────────────────────
// 1. Convert snake_case response data → camelCase
// 2. Normalize error messages for the hook layer

apiClient.interceptors.response.use(
    (response) => {
        // Convert response data: snake_case → camelCase
        if (response.data && typeof response.data === "object") {
            response.data = camelizeKeys(response.data) as typeof response.data;
        }
        return response;
    },
    (error) => {
        // Global 401 redirect
        if (error.response?.status === 401 && typeof window !== "undefined") {
            const isAuthPage = ["/login", "/register", "/verify-otp", "/confirm-email"].some(
                (path) => window.location.pathname.startsWith(path)
            );
            const isAuthRequest = ["/identity/login", "/identity/verify-otp", "/identity/google", "/identity/request-otp"].some(
                (url) => error.config?.url?.includes(url)
            );

            if (!isAuthPage && !isAuthRequest) {
                useAuthStore.getState().logout();
                window.location.href = "/login";
            }
        }

        // Normalize error message for hooks layer
        const message = error.response?.data?.message;
        const normalizedMessage = Array.isArray(message)
            ? message.join(". ")
            : message || "An unexpected error occurred.";

        return Promise.reject(normalizedMessage);
    }
);
