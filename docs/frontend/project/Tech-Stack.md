# Tech Stack "Super Speed" for Mini-ERP with AI

This project focuses on **High-Performance**, **Simplicity**, and **Accessibility**, using modern technologies to ensure a seamless experience for non-tech-savvy users.

## 1. Core Framework (The Turbo engine)
- **ReactJS (Vite)**: Fast development, lightweight SPA, zero-latency interactions.
- **TypeScript**: Robust type-safety for enterprise data structures.
- **React Router DOM v6+**: Seamless client-side routing.

## 2. UI & User Experience (Premium & Rapid)
- **Tailwind CSS**: Utility-first styling for fast rendering.
- **Shadcn UI**: Professional, accessible, lightweight component system.
- **Lucide React**: Clean, modern iconography.
- *(Note: Animations kept minimal using CSS transitions for better performance on low-end devices)*

## 3. Data & State Management (Caching-first)
- **TanStack Query (React Query) v5**: Powerful server-state caching and Optimistic Updates for instant UI feedback.
- **Zustand**: Minimalist client-state management for Sidebar and UI flows.
- **React Hook Form + Zod**: Efficient, type-safe form handling.

## 4. AI & Specialized Performance
- **Image Compression:** `browser-image-compression` to drastically reduce payload size before OCR processing.
- **Voice-to-Action:** Web Speech API (Local client-side STT) -> Send Text -> AI Backend.
- **OCR-to-Data:** Client simply uploads compressed image -> Azure Document Intelligence (Backend). *No heavy client-side OCR computation.*

## 5. Deployment & Target
- **Platform:** Web Dashboard (Left Sidebar layout). Mobile app will be built separately via Flutter later.
- **Hosting:** Vercel or similar fast CDN.