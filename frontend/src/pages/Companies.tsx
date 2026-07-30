import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { companiesAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { formatDate } from '../lib/utils'
import { Building2, Mail, Plus, Lock, CheckCircle2, Trash2, Loader2 } from 'lucide-react'
import { Button } from '../components/ui/button'
import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import AddCompanyModal from '../components/AddCompanyModal'

export default function Companies() {
  const [isAddCompanyOpen, setIsAddCompanyOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const queryClient = useQueryClient()

  const { data: companies, isLoading, refetch } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

  const deleteMutation = useMutation({
    mutationFn: (companyId: string) => companiesAPI.delete(companyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['b2b-leads'] })
      queryClient.invalidateQueries({ queryKey: ['b2c-leads'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      setDeletingId(null)
    },
    onError: (error: any) => {
      setDeletingId(null)
      const detail =
        error?.response?.data?.detail ||
        error?.message ||
        'Failed to delete company'
      alert(`Delete failed: ${detail}`)
    },
  })

  useEffect(() => {
    const oauth = searchParams.get('oauth')
    if (!oauth) return
    if (oauth === 'success') {
      alert('Gmail & Drive connected successfully.')
      refetch()
    } else {
      const message = searchParams.get('message') || 'unknown'
      alert(`OAuth failed: ${message}`)
    }
    setSearchParams({})
  }, [searchParams, setSearchParams, refetch])

  const handleConnectOAuth = (companyId: string) => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
    const apiBase = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
    // Prefer explicit n8n callback (local Docker). On Render, use backend callback.
    const redirectUri =
      import.meta.env.VITE_N8N_CALLBACK_URL ||
      `${apiBase}/api/companies/oauth/callback`

    if (!clientId) {
      alert(
        'OAuth configuration missing.\n\n' +
          'Set VITE_GOOGLE_CLIENT_ID on the frontend (Render Environment), ' +
          'then clear build cache and redeploy the frontend.'
      )
      return
    }

    const scopes = [
      'https://www.googleapis.com/auth/gmail.modify',
      'https://www.googleapis.com/auth/drive.readonly',
      'https://www.googleapis.com/auth/drive.file',
      'https://www.googleapis.com/auth/spreadsheets',
    ].join(' ')

    const googleOAuthUrl =
      `https://accounts.google.com/o/oauth2/v2/auth?` +
      `client_id=${encodeURIComponent(clientId)}&` +
      `redirect_uri=${encodeURIComponent(redirectUri)}&` +
      `response_type=code&` +
      `scope=${encodeURIComponent(scopes)}&` +
      `state=${encodeURIComponent(companyId)}&` +
      `access_type=offline&` +
      `prompt=consent`

    window.location.href = googleOAuthUrl
  }

  const handleDeleteCompany = (company: { company_id: string; name: string }) => {
    const confirmed = window.confirm(
      `Delete company "${company.name}"?\n\n` +
        'This permanently removes the company and all related emails, drafts, ' +
        'candidates, and audit logs from the database.\n\n' +
        'This cannot be undone.'
    )
    if (!confirmed) return
    setDeletingId(company.company_id)
    deleteMutation.mutate(company.company_id)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Companies</h1>
          <p className="text-gray-600">Manage all connected companies and their integrations</p>
        </div>
        <Button
          onClick={() => setIsAddCompanyOpen(true)}
          className="bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Company
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading companies...</div>
      ) : companies?.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {companies.map((company: any) => (
            <Card
              key={company.company_id}
              className="bg-white border-gray-200 hover:border-gray-300 transition-colors shadow-sm"
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div className="w-12 h-12 bg-gradient-to-br from-gray-300 to-gray-400 rounded-lg flex items-center justify-center shadow-md flex-shrink-0">
                      <Building2 className="w-6 h-6 text-gray-900" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <CardTitle className="text-gray-900 truncate">{company.name}</CardTitle>
                      <CardDescription className="flex items-center gap-1 mt-1 text-gray-600 truncate">
                        <Mail className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate">{company.email}</span>
                      </CardDescription>
                    </div>
                  </div>
                  <Badge
                    className={`${
                      company.status === 'active'
                        ? 'bg-green-500'
                        : 'bg-gray-400'
                    } text-white flex-shrink-0`}
                  >
                    {company.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between text-gray-600">
                      <span>OAuth Status</span>
                      {company.has_oauth_connected ? (
                        <Badge className="bg-green-500 text-white flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          Connected
                        </Badge>
                      ) : (
                        <Badge className="bg-yellow-500 text-white">Not Connected</Badge>
                      )}
                    </div>
                    {company.n8n_credential_id && (
                      <div className="flex items-center justify-between text-gray-600">
                        <span>Credential ID</span>
                        <span className="font-mono text-xs">{company.n8n_credential_id}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between text-gray-600">
                      <span>Created</span>
                      <span>{formatDate(company.created_at)}</span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    {!company.has_oauth_connected && (
                      <Button
                        onClick={() => handleConnectOAuth(company.company_id)}
                        className="w-full bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
                        size="sm"
                      >
                        <Lock className="w-4 h-4 mr-2" />
                        Connect Gmail & Drive
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800"
                      disabled={deletingId === company.company_id}
                      onClick={() =>
                        handleDeleteCompany({
                          company_id: company.company_id,
                          name: company.name,
                        })
                      }
                    >
                      {deletingId === company.company_id ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Deleting...
                        </>
                      ) : (
                        <>
                          <Trash2 className="w-4 h-4 mr-2" />
                          Delete Company
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Building2 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Companies Yet</h3>
            <p className="text-gray-600 mb-4">
              Get started by adding your first company
            </p>
            <Button
              onClick={() => setIsAddCompanyOpen(true)}
              className="bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Company
            </Button>
          </CardContent>
        </Card>
      )}

      <AddCompanyModal
        isOpen={isAddCompanyOpen}
        onClose={() => setIsAddCompanyOpen(false)}
        onConnect={() => {
          setIsAddCompanyOpen(false)
        }}
      />
    </div>
  )
}
