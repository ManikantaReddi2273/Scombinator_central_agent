import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { outboundAPI } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { X, Loader2, Mail, Calendar, FileText, MessageSquare } from 'lucide-react'
import { formatDate } from '../lib/utils'

interface OutboundCreateModalProps {
  lead: any
  companyId: string
  onClose: () => void
  onSuccess: (draftId: string) => void
}

export default function OutboundCreateModal({
  lead,
  companyId,
  onClose,
  onSuccess,
}: OutboundCreateModalProps) {
  const [selectedIntent, setSelectedIntent] = useState<string>('followup_checkin')

  // Fetch lead activities
  const { data: activities, isLoading: activitiesLoading } = useQuery({
    queryKey: ['lead-activities', companyId, lead.Lead_ID],
    queryFn: () => outboundAPI.getLeadActivities(companyId, lead.Lead_ID).then((res) => res.data),
  })

  // Create outbound email mutation (long timeout: Flow 2 can take 30–60s)
  const createMutation = useMutation({
    mutationFn: (intent: string) =>
      outboundAPI.createOutboundEmail({
        company_id: companyId,
        lead_id: String(lead.Lead_ID),
        email_type: 'B2B',
        intent: intent,
        trigger_type: 'manual',
      }),
    onSuccess: (response) => {
      const draftId = response?.data?.draft_id
      if (draftId) {
        onSuccess(draftId)
      } else {
        onClose()
      }
    },
    onError: () => {
      // Keep modal open so user sees error; they can click Cancel to close
    },
  })

  const intentOptions = [
    {
      value: 'followup_checkin',
      label: 'Follow-up Check-in',
      description: 'Check in on previous interaction',
      icon: MessageSquare,
    },
    {
      value: 'schedule_meeting',
      label: 'Schedule Meeting',
      description: 'Request a meeting or demo call',
      icon: Calendar,
    },
    {
      value: 'send_proposal',
      label: 'Send Proposal',
      description: 'Send proposal or pricing information',
      icon: FileText,
    },
    {
      value: 'address_objection',
      label: 'Address Objection',
      description: 'Respond to concerns or objections',
      icon: MessageSquare,
    },
  ]

  const handleCreate = () => {
    createMutation.mutate(selectedIntent)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-white border-gray-200 shadow-xl">
        <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200">
          <CardTitle className="text-xl font-bold text-gray-900">
            Send Email to {lead.Contact_Name}
          </CardTitle>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-gray-600 hover:text-gray-900"
          >
            <X className="w-5 h-5" />
          </Button>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {createMutation.isError && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-800">
              {createMutation.error?.response?.data?.detail ?? createMutation.error?.message ?? 'Failed to create draft. Please try again.'}
            </div>
          )}
          {/* Lead Details */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Lead Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Company:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Institution_Name}</span>
              </div>
              <div>
                <span className="text-gray-600">Contact:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Contact_Name}</span>
              </div>
              <div>
                <span className="text-gray-600">Role:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Role || 'N/A'}</span>
              </div>
              <div>
                <span className="text-gray-600">Email:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Email}</span>
              </div>
              <div>
                <span className="text-gray-600">Stage:</span>
                <Badge variant="outline" className="ml-2">
                  {lead.Stage || 'No Stage'}
                </Badge>
              </div>
              <div>
                <span className="text-gray-600">Engagement:</span>
                <Badge
                  variant="outline"
                  className={
                    lead.Engagement_Level === 'High'
                      ? 'ml-2 border-green-500 text-green-700'
                      : 'ml-2'
                  }
                >
                  {lead.Engagement_Level || 'Medium'}
                </Badge>
              </div>
              {lead.Last_Activity_Date && (
                <div>
                  <span className="text-gray-600">Last Activity:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {formatDate(lead.Last_Activity_Date)}
                  </span>
                </div>
              )}
              {lead.Next_Followup_Date && (
                <div>
                  <span className="text-gray-600">Next Follow-up:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {formatDate(lead.Next_Followup_Date)}
                  </span>
                </div>
              )}
            </div>
            {lead.Notes && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Notes:</span>
                <p className="text-sm text-gray-600 mt-1">{lead.Notes}</p>
              </div>
            )}
            {lead.Objection_Notes && (
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <span className="text-sm font-medium text-yellow-800">Objection Notes:</span>
                <p className="text-sm text-yellow-700 mt-1">{lead.Objection_Notes}</p>
              </div>
            )}
          </div>

          {/* Recent Activities */}
          {activitiesLoading ? (
            <div className="text-center py-4 text-gray-500">Loading activities...</div>
          ) : activities && activities.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Recent Activities</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {activities.slice(0, 3).map((activity: any) => (
                  <div
                    key={activity.Activity_ID}
                    className="p-2 bg-gray-50 rounded-lg text-sm border border-gray-200"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">
                        {activity.Activity_Type || 'Activity'}
                      </span>
                      {activity.Activity_Date && (
                        <span className="text-gray-500 text-xs">
                          {formatDate(activity.Activity_Date)}
                        </span>
                      )}
                    </div>
                    {activity.Summary && (
                      <p className="text-gray-600 mt-1 text-xs">{activity.Summary}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Intent Selection */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Email Intent</h3>
            <div className="grid grid-cols-2 gap-3">
              {intentOptions.map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.value}
                    onClick={() => setSelectedIntent(option.value)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedIntent === option.value
                        ? 'border-gray-400 bg-gray-50 shadow-md'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <Icon
                        className={`w-5 h-5 mt-0.5 ${
                          selectedIntent === option.value ? 'text-gray-900' : 'text-gray-600'
                        }`}
                      />
                      <div>
                        <div
                          className={`font-medium ${
                            selectedIntent === option.value ? 'text-gray-900' : 'text-gray-700'
                          }`}
                        >
                          {option.label}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">{option.description}</div>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <Button variant="outline" onClick={onClose} disabled={createMutation.isPending}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending}
              className="bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4 mr-2" />
                  Create Draft
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

