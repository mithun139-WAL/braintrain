import { create } from "zustand";

interface UiState {
    isSidebarOpen: boolean;
    activeModal: string | null;
    setSidebarOpen: (isOpen: boolean) => void;
    openSidebar: () => void;
    closeSidebar: () => void;
    toggleSidebar: () => void;
    openModal: (modalId: string) => void;
    closeModal: () => void;
}

export const useUiStore = create<UiState>((set) => ({
    isSidebarOpen: false,
    activeModal: null,
    setSidebarOpen: (isSidebarOpen) => set({ isSidebarOpen }),
    openSidebar: () => set({ isSidebarOpen: true }),
    closeSidebar: () => set({ isSidebarOpen: false }),
    toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
    openModal: (modalId) => set({ activeModal: modalId }),
    closeModal: () => set({ activeModal: null }),
}));
