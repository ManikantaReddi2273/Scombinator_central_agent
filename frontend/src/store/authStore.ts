import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface AuthState {
  token: string | null
  adminEmail: string | null
  role: string | null
  isAuthenticated: boolean
  login: (token: string, email: string, role: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      adminEmail: null,
      role: null,
      isAuthenticated: false,
      login: (token, email, role) =>
        set({
          token,
          adminEmail: email,
          role,
          isAuthenticated: true,
        }),
      logout: () =>
        set({
          token: null,
          adminEmail: null,
          role: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

