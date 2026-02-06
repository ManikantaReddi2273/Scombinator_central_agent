import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { X, Building2, Mail, Lock } from 'lucide-react'

interface AddCompanyModalProps {
  isOpen: boolean
  onClose: () => void
  onConnect: (companyName: string) => void
}

export default function AddCompanyModal({ isOpen, onClose }: AddCompanyModalProps) {
  const [companyName, setCompanyName] = useState('')
  const [loading, setLoading] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!companyName.trim()) return

    setLoading(true)
    try {
      // Get Google OAuth credentials from environment variables
      // These should be set in your .env file
      const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
      const redirectUri = import.meta.env.VITE_N8N_CALLBACK_URL || 'http://localhost:5678/webhook/oauth-callback'
      
      if (!clientId) {
        console.error('Google Client ID not configured. Please set VITE_GOOGLE_CLIENT_ID in .env file')
        alert('OAuth configuration missing. Please contact administrator.')
        setLoading(false)
        return
      }
      
      // Store company name in sessionStorage for later use (backup)
      sessionStorage.setItem('pending_company_name', companyName.trim())
      
      // Build Google OAuth URL
      // The 'state' parameter will contain the company name
      // After OAuth, Google redirects to n8n webhook with code and state
      const scopes = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.file'
      ].join(' ')
      
      const googleOAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
        `client_id=${encodeURIComponent(clientId)}&` +
        `redirect_uri=${encodeURIComponent(redirectUri)}&` +
        `response_type=code&` +
        `scope=${encodeURIComponent(scopes)}&` +
        `state=${encodeURIComponent(companyName.trim())}&` +
        `access_type=offline&` + // Required to get refresh token
        `prompt=consent` // Force consent screen to ensure refresh token
      
      // Redirect to Google OAuth
      window.location.href = googleOAuthUrl
    } catch (error) {
      console.error('Error initiating OAuth:', error)
      alert('Failed to initiate OAuth. Please try again.')
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
              <CardDescription>Connect Gmail and Drive for automation</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="companyName" className="text-sm font-medium text-gray-700">
                Company Name
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
                />
              </div>
              <p className="text-xs text-gray-500">
                Enter the company name. You'll connect their Gmail and Drive next.
              </p>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-200">
                <Mail className="w-5 h-5 text-gray-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 mb-1">What happens next?</p>
                  <ul className="text-xs text-gray-700 space-y-1">
                    <li>• You'll be redirected to Google OAuth</li>
                    <li>• Sign in with the company's Gmail account</li>
                    <li>• Grant access to Gmail and Drive</li>
                    <li>• Company will be automatically registered</li>
                  </ul>
                </div>
              </div>
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
                disabled={loading || !companyName.trim()}
              >
                {loading ? (
                  <>Connecting...</>
                ) : (
                  <>
                    <Lock className="w-4 h-4 mr-2" />
                    Connect Gmail & Drive
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

