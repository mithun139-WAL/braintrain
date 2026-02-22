import { create } from "zustand";

interface UiState {
    isSidebarOpen: boolean;
    activeModal: string | null;
    toggleSidebar: () => void;
    openModal: (modalId: string) => void;
    closeModal: () => void;
}

export const useUiStore = create<UiState>((set) => ({
    isSidebarOpen: true,
    activeModal: null,
    toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
    openModal: (modalId) => set({ activeModal: modalId }),
    closeModal: () => set({ activeModal: null }),
}));
