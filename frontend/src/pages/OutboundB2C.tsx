import { useQuery, useQueryClient } from '@tanstack/react-query'
import { outboundAPI, companiesAPI } from '../lib/api'
import { Card, CardContent } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Button } from '../components/ui/button'
import { formatDate } from '../lib/utils'
import { Mail, Users, Send, Filter, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import OutboundB2CCreateModal from '../components/OutboundB2CCreateModal'

export default function OutboundB2C() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [selectedLead, setSelectedLead] = useState<any>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

  const { data: leads, isLoading } = useQuery({
    queryKey: ['b2c-leads', selectedCompany],
    queryFn: () => {
      if (!selectedCompany) return Promise.resolve([])
      return outboundAPI.getB2CLeads(selectedCompany).then((res) => res.data)
    },
    enabled: !!selectedCompany,
  })

  const stoppedStatus = 'No Response – Outreach Stopped'
  const isOutreachStopped = (lead: any) =>
    (lead?.Status || '').trim() === stoppedStatus ||
    (lead?.Stage || '').trim() === stoppedStatus

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

  const b2cLeadId = (lead: any) => lead?.B2C_Lead_ID ?? lead?.b2c_lead_id ?? ''

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">B2C Outreach</h1>
        <p className="text-gray-600">
          Reach people who commented on your social posts (LinkedIn, Instagram, etc.). Send post-context emails from brand context.
        </p>
      </div>

      <Card className="bg-white border-gray-200 shadow-sm">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm text-gray-700 font-medium">Select company:</span>
            </div>
            <Button
              variant={!selectedCompany ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedCompany(null)}
            >
              All companies
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

      {!selectedCompany ? (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Users className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Select a company to view B2C leads</p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <Card className="bg-white border-gray-200">
          <CardContent className="p-12 text-center">
            <Loader2 className="w-8 h-8 mx-auto text-gray-400 mb-4 animate-spin" />
            <p className="text-gray-500">Loading B2C leads...</p>
          </CardContent>
        </Card>
      ) : leads?.length > 0 ? (
        <div className="space-y-3">
          {leads.map((lead: any) => (
            <Card
              key={b2cLeadId(lead)}
              className="bg-white border-gray-200 hover:border-gray-300 transition-colors shadow-sm"
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {lead.Name ?? lead.Email}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-2 flex-wrap">
                          <div className="flex items-center gap-1">
                            <Mail className="w-4 h-4" />
                            {lead.Email}
                          </div>
                          {lead.Source && <span>Source: {lead.Source}</span>}
                          {lead.Campaign && <span>Campaign: {lead.Campaign}</span>}
                          {lead.Last_Activity_Date && (
                            <span>Last activity: {formatDate(lead.Last_Activity_Date)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap mb-3">
                      <Badge variant="outline" className="border-gray-300 text-gray-700">
                        {lead.Stage ?? '—'}
                      </Badge>
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
                        {lead.Status ?? '—'}
                      </Badge>
                      {typeof lead.Follow_Up_Count === 'number' && lead.Follow_Up_Count > 0 && (
                        <Badge variant="outline" className="border-slate-400 text-slate-600">
                          Follow-up {lead.Follow_Up_Count} sent
                        </Badge>
                      )}
                    </div>
                    {lead.Notes && (
                      <p className="text-sm text-gray-600 line-clamp-2">{lead.Notes}</p>
                    )}
                    {lead.Next_Followup_Date && (
                      <p className="text-sm text-gray-600 mt-1">
                        Next follow-up: {formatDate(lead.Next_Followup_Date)}
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
                      Send email
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
            <Users className="w-16 h-16 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No B2C leads for this company</p>
            <p className="text-sm text-gray-400 mt-2">
              Ensure the CRM workbook has a B2C_FUNNEL worksheet with columns: B2C_Lead_ID, Name, Email, Source, Campaign_id, Campaign, Stage, Notes, Follow_Up_Count, etc.
            </p>
          </CardContent>
        </Card>
      )}

      {showCreateModal && selectedLead && (
        <OutboundB2CCreateModal
          lead={selectedLead}
          companyId={selectedCompany!}
          onClose={handleModalClose}
          onSuccess={handleCreateSuccess}
        />
      )}
    </div>
  )
}
