"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@braintrain/shared";

interface AuthState {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    hasHydrated: boolean;
    setAuth: (user: User, token: string) => void;
    setHasHydrated: (state: boolean) => void;
    clearAuth: () => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            token: null,
            isAuthenticated: false,
            hasHydrated: false,
            setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
            setHasHydrated: (state) => set({ hasHydrated: state }),
            clearAuth: () => set({ user: null, token: null, isAuthenticated: false }),
            logout: () => set({ user: null, token: null, isAuthenticated: false }),
        }),
        {
            name: "braintrain-auth-storage",
            onRehydrateStorage: (state) => {
                return () => state?.setHasHydrated(true);
            },
        }
    )
);
