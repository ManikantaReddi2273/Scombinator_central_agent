import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { X, Building2, Mail } from 'lucide-react'
import { companiesAPI } from '../lib/api'
import { useQueryClient } from '@tanstack/react-query'

interface AddCompanyModalProps {
  isOpen: boolean
  onClose: () => void
  onConnect: (companyName: string) => void
}

export default function AddCompanyModal({ isOpen, onClose }: AddCompanyModalProps) {
  const [companyName, setCompanyName] = useState('')
  const [companyEmail, setCompanyEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!companyName.trim() || !companyEmail.trim()) return

    setLoading(true)
    setError(null)
    
    try {
      // Step 1: Create company directly via backend API
      await companiesAPI.create({
        name: companyName.trim(),
        email: companyEmail.trim()
      })
      
      // Refresh companies list
      await queryClient.invalidateQueries({ queryKey: ['companies'] })
      
      // Close modal and reset form
      setCompanyName('')
      setCompanyEmail('')
      onClose()
    } catch (err: any) {
      console.error('Error creating company:', err)
      setError(err.response?.data?.detail || 'Failed to create company. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-md bg-white border-gray-200 shadow-2xl">
        <CardHeader className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
            onClick={onClose}
          >
            <X className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-gray-300 to-gray-400 rounded-lg flex items-center justify-center">
              <Building2 className="w-6 h-6 text-gray-900" />
            </div>
            <div>
              <CardTitle className="text-gray-900">Add New Company</CardTitle>
            <CardDescription>Register a new company (OAuth can be connected later)</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
            
            <div className="space-y-2">
              <label htmlFor="companyName" className="text-sm font-medium text-gray-700">
                Company Name *
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  id="companyName"
                  type="text"
                  placeholder="e.g., AlphaTech"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="pl-10 bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-gray-400"
                  required
                  autoFocus
                  disabled={loading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="companyEmail" className="text-sm font-medium text-gray-700">
                Company Email *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  id="companyEmail"
                  type="email"
                  placeholder="e.g., contact@alphatech.com"
                  value={companyEmail}
                  onChange={(e) => setCompanyEmail(e.target.value)}
                  className="pl-10 bg-white border-gray-300 text-gray-900 placeholder:text-gray-400 focus:border-gray-400"
                  required
                  disabled={loading}
                />
              </div>
              <p className="text-xs text-gray-500">
                This email will be used for Gmail integration. You can connect OAuth later.
              </p>
            </div>

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                className="flex-1"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="flex-1 bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
                disabled={loading || !companyName.trim() || !companyEmail.trim()}
              >
                {loading ? (
                  <>Creating...</>
                ) : (
                  <>
                    <Building2 className="w-4 h-4 mr-2" />
                    Create Company
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

