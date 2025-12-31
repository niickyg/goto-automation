import { create } from 'zustand'

export const useAppStore = create((set) => ({
  // UI State
  sidebarOpen: true,
  darkMode: false,
  
  // Filters
  selectedPeriod: 'week',
  searchQuery: '',
  activeFilters: {},
  
  // Actions
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  setPeriod: (period) => set({ selectedPeriod: period }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setFilters: (filters) => set({ activeFilters: filters }),
  clearFilters: () => set({ activeFilters: {} }),
}))
