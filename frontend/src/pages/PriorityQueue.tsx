import { useQuery } from '@tanstack/react-query'
import { emailsAPI, draftsAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { formatDate, getPriorityColor, getStatusColor } from '../lib/utils'
import { Mail, Building2, Clock, FileText, ExternalLink } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function PriorityQueue() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const navigate = useNavigate()
  
  const { data: queue, isLoading } = useQuery({
    queryKey: ['priority-queue', selectedCompany],
    queryFn: () => emailsAPI.getPriorityQueue(50).then((res) => res.data),
  })

  // Fetch drafts for all emails to show draft status
  const { data: allDrafts } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => draftsAPI.list().then((res) => res.data),
  })

  // Create a map of email_id -> draft
  const emailDraftMap = new Map()
  allDrafts?.forEach((draft: any) => {
    if (draft.email_id) {
      emailDraftMap.set(draft.email_id, draft)
    }
  })

  const filteredQueue = selectedCompany
    ? queue?.filter((item: any) => item.company_id === selectedCompany)
    : queue

  // Get unique companies by company_id (deduplicate)
  const companyMap = new Map<string, { id: string; name: string }>()
  queue?.forEach((item: any) => {
    if (item.company_id && item.company_name && !companyMap.has(item.company_id)) {
      companyMap.set(item.company_id, {
        id: item.company_id,
        name: item.company_name,
      })
    }
  })
  const companies = Array.from(companyMap.values())

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Priority Queue</h1>
          <p className="text-gray-600">Unified cross-company priority queue sorted by importance</p>
        </div>
      </div>

      {/* Company Filter */}
      {companies.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedCompany(null)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              !selectedCompany
                ? 'bg-gray-300 text-gray-900 shadow-md'
                : 'bg-white text-gray-700 hover:bg-[#EAEFEF] border border-gray-300'
            }`}
          >
            All Companies
          </button>
          {companies.map((company: any) => (
            <button
              key={company.id}
              onClick={() => setSelectedCompany(company.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCompany === company.id
                  ? 'bg-gray-300 text-gray-900 shadow-md'
                  : 'bg-white text-gray-700 hover:bg-[#EAEFEF] border border-gray-300'
              }`}
            >
              {company.name}
            </button>
          ))}
        </div>
      )}

      {/* Queue Items */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading...</div>
        ) : filteredQueue?.length > 0 ? (
          filteredQueue.map((item: any) => (
            <Card
              key={item.email_id}
              className="bg-white border-gray-200 hover:border-gray-300 transition-colors shadow-sm"
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`w-16 h-16 rounded-lg flex items-center justify-center text-white font-bold text-lg ${getPriorityColor(item.priority_score)}`}>
                    {item.priority_score}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">{item.subject}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Building2 className="w-4 h-4" />
                            {item.company_name}
                          </div>
                          <div className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {item.from_email}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatDate(item.created_at)}
                          </div>
                        </div>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-3">{item.executive_summary}</p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {item.function}
                      </Badge>
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {item.intent}
                      </Badge>
                      <Badge variant="outline" className="border-gray-400 text-gray-700">
                        {item.recommended_action}
                      </Badge>
                      {/* Draft Status */}
                      {emailDraftMap.has(item.email_id) && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs h-6"
                          onClick={() => navigate(`/drafts?draft=${emailDraftMap.get(item.email_id).id}`)}
                        >
                          <FileText className="w-3 h-3 mr-1" />
                          Draft: {emailDraftMap.get(item.email_id).status}
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </Button>
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
              <p className="text-gray-500">No items in priority queue</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

