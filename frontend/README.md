# College Management System (CMS) Frontend

This is the frontend application for the College Management System (CMS) redesign. It is built with **React**, **TypeScript**, **Vite**, and **Tailwind CSS**, providing a dynamic, responsive, and secure user experience for administrators, staff, and students.

---

## 🛠️ Technology Stack

- **Framework & Build Tool**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS, PostCSS, Lucide React (Icons)
- **Routing**: React Router DOM (v6)
- **State Management & Data Fetching**: TanStack React Query (v5)
- **Form Handling & Validation**: React Hook Form, Zod
- **HTTP Client**: Axios (with custom token refresh interceptors)

---

## 📂 Project Structure

```text
frontend/
├── src/
│   ├── components/      # Reusable UI components (Sidebar, Navbar, Cards, Tables)
│   ├── lib/             # API client, Authentication Context, helpers
│   │   ├── api.ts       # Axios client with interceptors for token refresh
│   │   ├── auth.ts      # LocalStorage managers for JWTs
│   │   └── AuthContext.tsx # Context provider for global user state
│   ├── pages/           # Page components grouped by domain
│   │   ├── academics/   # Academic management (Institutes, Programs, Sessions, Specializations)
│   │   ├── lms/         # Leave Management System (Leaves, approvals, balance)
│   │   ├── AdminDashboard.tsx
│   │   ├── StudentDashboard.tsx
│   │   ├── StaffDashboard.tsx
│   │   ├── StudentManagement.tsx
│   │   ├── StaffManagement.tsx
│   │   ├── Feedback360.tsx # 360-degree feedback system
│   │   └── Login.tsx
│   ├── App.tsx          # Main application router and shell
│   └── main.tsx         # Entry point
```

---

## ⚙️ Prerequisites

- **Node.js**: v18.x or v20.x
- **npm** or **yarn**
- **Running Backend API**: The frontend expects a running backend service (default: `http://localhost:8000/api/v1`).

---

## 🚀 Getting Started

### 1. Install Dependencies
From the `frontend` directory, install the required packages:
```bash
npm install
```

### 2. Configure Environment Variables
Create a `.env` file in the `frontend` root directory:
```env
VITE_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server
Start Vite's development server locally:
```bash
npm run dev
```
The application will be accessible at: [http://localhost:5173](http://localhost:5173)

---

## 🔧 Scripts

- `npm run dev`: Start the development server with hot-reload.
- `npm run build`: Compile TypeScript and build production assets into `dist/`.
- `npm run lint`: Lint code with ESLint.
- `npm run preview`: Run a local server to preview the production build.

---

## 🔐 Authentication & Session Flow

1. **Login**: User logs in via the login interface. The API returns an `access_token` and `refresh_token`.
2. **Access token**: Stored securely and attached to every API request using an Axios Request Interceptor.
3. **Token Refresh**: If an API call fails with a `401 Unauthorized` status (expired access token), an Axios Response Interceptor automatically intercepts the response, requests a new access token using the refresh token, updates local storage, and retries the failed request seamlessly.
4. **Role-Based Routing**: Paths are protected using role checks. Accessing a dashboard requires the correct user role; otherwise, the user is redirected to `/unauthorized` or `/login`.
