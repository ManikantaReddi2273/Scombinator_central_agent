# S Combinator Central Agent Platform - Frontend

Modern React frontend dashboard for the S Combinator Central Agent Platform.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Query** - Data fetching
- **Zustand** - State management
- **React Router v6** - Routing
- **Lucide React** - Icons

## Setup

### 1. Install Dependencies

```bash
npm install
```

Or with yarn:

```bash
yarn install
```

### 2. Configure Environment

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Features

### ✅ Implemented

- **Login Page** - Admin authentication
- **Dashboard** - Overview with stats and quick views
- **Priority Queue** - Unified cross-company priority queue
- **Draft Management** - View, edit, approve, and reject drafts
- **Email Views** - List emails with filters
- **Company Management** - View all connected companies
- **Responsive Design** - Works on desktop and mobile
- **Dark Theme** - Modern industrial look

### 🎨 Design Features

- Dark theme with purple/blue gradient accents
- Smooth animations and transitions
- Professional, industrial-level UI
- Responsive sidebar navigation
- Real-time data updates
- Clean, modern interface

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/          # Reusable UI components
│   ├── pages/           # Page components
│   ├── layouts/         # Layout components
│   ├── store/           # Zustand stores
│   ├── lib/             # Utilities and API client
│   ├── App.tsx          # Main app component
│   └── main.tsx         # Entry point
├── public/
└── package.json
```

## Pages

1. **Login** (`/login`) - Admin login
2. **Dashboard** (`/`) - Overview and stats
3. **Priority Queue** (`/priority-queue`) - Cross-company priority queue
4. **Drafts** (`/drafts`) - Draft management and approval
5. **Emails** (`/emails`) - Email listing with filters
6. **Companies** (`/companies`) - Company management

## API Integration

All API calls are handled through `src/lib/api.ts` which uses Axios with:
- Automatic JWT token injection
- 401 error handling (redirects to login)
- TypeScript types

## State Management

- **Zustand** for authentication state (persisted to localStorage)
- **React Query** for server state (caching, refetching, etc.)

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Development

The frontend proxies API requests to `http://localhost:8000` (configured in `vite.config.ts`).

Make sure the backend is running on port 8000 before starting the frontend.

