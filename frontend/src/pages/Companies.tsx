import { useQuery } from '@tanstack/react-query'
import { companiesAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { formatDate } from '../lib/utils'
import { Building2, Mail, Plus } from 'lucide-react'
import { Button } from '../components/ui/button'
import { useState } from 'react'
import AddCompanyModal from '../components/AddCompanyModal'

export default function Companies() {
  const [isAddCompanyOpen, setIsAddCompanyOpen] = useState(false)
  
  const { data: companies, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

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
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-gradient-to-br from-gray-300 to-gray-400 rounded-lg flex items-center justify-center shadow-md">
                      <Building2 className="w-6 h-6 text-gray-900" />
                    </div>
                    <div>
                      <CardTitle className="text-gray-900">{company.name}</CardTitle>
                      <CardDescription className="flex items-center gap-1 mt-1 text-gray-600">
                        <Mail className="w-3 h-3" />
                        {company.email}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge
                    className={`${
                      company.status === 'active'
                        ? 'bg-green-500'
                        : 'bg-gray-400'
                    } text-white`}
                  >
                    {company.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between text-gray-600">
                    <span>Credential ID</span>
                    <span className="font-mono text-xs">{company.n8n_credential_id || 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between text-gray-600">
                    <span>Connected</span>
                    <span>{formatDate(company.created_at)}</span>
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
              Companies will be added automatically when n8n completes OAuth flow
            </p>
            <p className="text-sm text-gray-500">
              Use n8n workflows to connect company Gmail and Drive accounts
            </p>
          </CardContent>
        </Card>
      )}

      {/* Add Company Modal */}
      <AddCompanyModal
        isOpen={isAddCompanyOpen}
        onClose={() => setIsAddCompanyOpen(false)}
        onConnect={(companyName) => {
          setIsAddCompanyOpen(false)
          // OAuth redirect will happen in the modal
        }}
      />
    </div>
  )
}

