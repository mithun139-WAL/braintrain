# BrainTrain Web — Architecture Documentation

This document outlines the architecture and technical decisions for the BrainTrain web application.

## Technology Stack

- **Framework**: [Next.js](https://nextjs.org/) (v16.1.6) using the **App Router**.
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) for utility-first styling.
- **State Management**: [Zustand](https://github.com/pmndrs/zustand) for lightweight client-side state.
- **Data Fetching**: [React Query](https://tanstack.com/query/latest) (TanStack Query) for server state management and caching.
- **API Client**: [Axios](https://axios-http.com/) for HTTP requests.
- **Icons**: [Lucide React](https://lucide.dev/) for consistent iconography.
- **Theming**: [next-themes](https://github.com/pacocoursey/next-themes) for dark/light mode support.

## Directory Structure

```text
apps/web/
├── app/                 # Next.js App Router (pages and layouts)
│   ├── (auth)/          # Authentication routes (login, register)
│   ├── (dashboard)/     # Post-login dashboard routes
│   └── layout.tsx       # Root layout with providers
├── components/          # Reusable UI components
├── designs/             # Design assets and mockups
├── lib/                 # Utility functions and shared helpers
├── providers/           # React Context providers (QueryClient, etc.)
├── proxy.ts             # API proxy configuration
├── public/              # Static assets (images, fonts)
└── styles/              # Global CSS and Tailwind configurations
```

## Key Architectural Patterns

### 1. App Router & Route Groups
We use Next.js Route Groups (e.g., `(auth)`, `(dashboard)`) to logically separate concerns without affecting the URL structure. This allows for shared layouts within specific application areas.

### 2. Server State Management
`React Query` is used for all API interactions. It handles:
- Automatic caching and revalidation.
- Loading and error states.
- Optimistic updates for a smoother user experience.

### 3. Shared Types & Contracts
The web app depends on `@braintrain/shared` for all API DTOs and Enums. This ensures that the frontend is always in sync with the backend contracts, preventing runtime errors due to mismatched data shapes.

### 4. Component Philosophy
- **UI Components**: Atomic components in `components/` (Buttons, Cards, Modals).
- **Feature Components**: Larger components that pull in data or manage specific feature logic.
- **Layouts**: Define the shell for different parts of the application.

## Core Feature Modules

1. **Interactive Interview Interface (`/dashboard/sessions/active`)**: Supports both text and audio response simulations with real-time timers and dynamic layout changes based on the configured AI persona.
2. **AI Evaluation Dashboard (`/dashboard/sessions/evaluation`)**: Aggregates completion scores from the backend, rendering comparative radial charts across communication, technical depth, and system design alongside specific AI contextual feedback.
3. **Performance Trends Analytics (`/dashboard/trends`)**: Visualizes historical mock interview progression, plotting adaptive difficulty journey maps and weakness detection graphs utilizing scalable vector SVGs and React hooks.
4. **Unified Settings Console (`/dashboard/settings`)**: Tab-driven unified interface for resolving profile management, secure subscription/billing history rendering, and overriding granular simulated AI behavior preferences.

## Communication with Backend

Transitioning from local state to the backend involves:
1.  **Defining DTOs** in `packages/shared`.
2.  **Implementing API calls** in `lib/api/` (or similar) using Axios.
3.  **Wrapping calls** with React Query hooks for use in components.

## Development

Run the development server:
```bash
pnpm dev
```
