import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { outboundAPI, companiesAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { formatDate } from '../lib/utils'
import { Mail, Building2, Send, Filter, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import OutboundCreateModal from '../components/OutboundCreateModal'

export default function OutboundB2B() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [selectedLead, setSelectedLead] = useState<any>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Fetch companies
  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

  // Fetch B2B leads
  const { data: leads, isLoading } = useQuery({
    queryKey: ['b2b-leads', selectedCompany],
    queryFn: () => {
      if (!selectedCompany) {
        return Promise.resolve([])
      }
      return outboundAPI.getB2BLeads(selectedCompany).then((res) => res.data)
    },
    enabled: !!selectedCompany,
  })

  const isOutreachStopped = (lead: any) =>
    (lead?.Status || '').trim() === 'No Response – Outreach Stopped' ||
    (lead?.Stage || '').trim() === 'No Response – Outreach Stopped'

  const handleSendEmail = (lead: any) => {
    setSelectedLead(lead)
    setShowCreateModal(true)
  }

  const handleModalClose = () => {
    setShowCreateModal(false)
    setSelectedLead(null)
  }

  const handleCreateSuccess = (draftId: string) => {
    queryClient.invalidateQueries({ queryKey: ['drafts'] })
    handleModalClose()
    navigate(`/drafts?draft=${draftId}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">B2B Outbound Leads</h1>
        <p className="text-gray-600">Manage B2B leads and send outbound emails</p>
      </div>

      {/* Company Selector */}
      <Card className="bg-white border-gray-200 shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700 font-medium">Select Company:</span>
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
          </div>
        </CardContent>
      </Card>

      {/* Leads List */}
      {!selectedCompany ? (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Building2 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Please select a company to view leads</p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Loader2 className="w-8 h-8 mx-auto text-gray-400 mb-4 animate-spin" />
            <p className="text-gray-500">Loading leads...</p>
          </CardContent>
        </Card>
      ) : leads?.length > 0 ? (
        <div className="space-y-3">
          {leads.map((lead: any) => (
            <Card
              key={lead.Lead_ID}
              className="bg-white border-gray-200 hover:border-gray-300 transition-colors shadow-sm"
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {lead.Institution_Name || 'Unknown Company'}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-2 flex-wrap">
                          <div className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {lead.Email}
                          </div>
                          <span>Contact: {lead.Contact_Name}</span>
                          {lead.Role && <span>Role: {lead.Role}</span>}
                          {lead.Last_Activity_Date && (
                            <span>Last Activity: {formatDate(lead.Last_Activity_Date)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap mb-3">
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {lead.Stage || 'No Stage'}
                      </Badge>
                      <Badge
                        variant="outline"
                        className={
                          lead.Engagement_Level === 'High'
                            ? 'border-green-500 text-green-700'
                            : 'border-gray-300 text-gray-700'
                        }
                      >
                        {lead.Engagement_Level || 'Medium'}
                      </Badge>
                      {lead.Proposal_Value && (
                        <Badge variant="outline" className="border-blue-500 text-blue-700">
                          ₹{lead.Proposal_Value}
                        </Badge>
                      )}
                      <Badge
                        variant="outline"
                        className={
                          lead.Status === 'Active'
                            ? 'border-green-500 text-green-700'
                            : isOutreachStopped(lead)
                              ? 'border-amber-600 text-amber-700 bg-amber-50'
                              : 'border-gray-300 text-gray-700'
                        }
                      >
                        {lead.Status || 'Unknown'}
                      </Badge>
                      {typeof lead.Follow_Up_Count === 'number' && lead.Follow_Up_Count > 0 && (
                        <Badge variant="outline" className="border-slate-400 text-slate-600">
                          Follow-up {lead.Follow_Up_Count} sent
                        </Badge>
                      )}
                    </div>
                    {lead.Next_Followup_Date && (
                      <p className="text-sm text-gray-600">
                        Next Follow-up: {formatDate(lead.Next_Followup_Date)}
                      </p>
                    )}
                  </div>
                  {isOutreachStopped(lead) ? (
                    <span className="text-sm text-amber-700 font-medium px-3 py-2 border border-amber-200 rounded-md bg-amber-50">
                      Outreach stopped
                    </span>
                  ) : (
                    <Button
                      onClick={() => handleSendEmail(lead)}
                      className="bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      Send Email
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Building2 className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No B2B leads found for this company</p>
            <p className="text-sm text-gray-400 mt-2">
              Make sure CRM/LEADS.xlsx exists in the company's Google Drive folder
            </p>
          </CardContent>
        </Card>
      )}

      {/* Create Modal */}
      {showCreateModal && selectedLead && (
        <OutboundCreateModal
          lead={selectedLead}
          companyId={selectedCompany!}
          onClose={handleModalClose}
          onSuccess={handleCreateSuccess}
        />
      )}
    </div>
  )
}

