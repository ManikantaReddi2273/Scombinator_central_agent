import { useQuery } from '@tanstack/react-query'
import { emailsAPI } from '../lib/api'
import { Card, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { formatDate, getPriorityColor } from '../lib/utils'
import { Mail, Building2, Filter } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../components/ui/button'

export default function Emails() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [selectedFunction, setSelectedFunction] = useState<string | null>(null)

  const { data: emails, isLoading } = useQuery({
    queryKey: ['emails', selectedCompany, selectedFunction],
    queryFn: () =>
      emailsAPI
        .list({
          company_id: selectedCompany || undefined,
          function: selectedFunction || undefined,
          limit: 50,
        })
        .then((res) => res.data),
  })

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

  const functions = ['Sales', 'Hiring', 'Legal', 'Support', 'Ops', 'Marketing', 'Admin']

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Emails</h1>
        <p className="text-gray-600">View and manage all processed emails</p>
      </div>

      {/* Filters */}
      <Card className="bg-white border-gray-200 shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700">Filters:</span>
            </div>
            <Button
              variant={!selectedCompany ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCompany(null)}
            >
              All Companies
            </Button>
            {companies?.map((company: any) => (
              <Button
                key={company.company_id}
                variant={selectedCompany === company.company_id ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedCompany(company.company_id)}
              >
                {company.name}
              </Button>
            ))}
            <div className="ml-4 flex items-center gap-2">
              <span className="text-sm text-gray-700">Function:</span>
              <Button
                variant={!selectedFunction ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedFunction(null)}
              >
                All
              </Button>
              {functions.map((func) => (
                <Button
                  key={func}
                  variant={selectedFunction === func ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedFunction(func)}
                >
                  {func}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Emails List */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading emails...</div>
        ) : emails?.length > 0 ? (
          emails.map((email: any) => (
            <Card
              key={email.id}
              className="bg-white border-gray-200 hover:border-gray-300 transition-colors shadow-sm"
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold ${getPriorityColor(email.priority_score)}`}
                  >
                    {email.priority_score}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">{email.subject}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                          <div className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {email.from_email}
                          </div>
                          <span>{formatDate(email.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    {email.executive_summary && (
                      <p className="text-gray-700 mb-3">{email.executive_summary}</p>
                    )}
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {email.function}
                      </Badge>
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {email.intent}
                      </Badge>
                      {email.recommended_action && (
                        <Badge variant="outline" className="border-gray-400 text-gray-700">
                          {email.recommended_action}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card className="bg-white border-gray-200">
            <CardContent className="p-12 text-center">
              <Mail className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">No emails found</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

