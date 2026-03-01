import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { outboundAPI } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { X, Loader2, Mail } from 'lucide-react'
import { formatDate } from '../lib/utils'

interface OutboundB2CCreateModalProps {
  lead: any
  companyId: string
  onClose: () => void
  onSuccess: (draftId: string) => void
}

export default function OutboundB2CCreateModal({
  lead,
  companyId,
  onClose,
  onSuccess,
}: OutboundB2CCreateModalProps) {
  const createMutation = useMutation({
    mutationFn: () =>
      outboundAPI.createOutboundEmail({
        company_id: companyId,
        lead_id: String(lead.B2C_Lead_ID ?? lead.b2c_lead_id),
        email_type: 'B2C',
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
  })

  const handleCreate = () => {
    createMutation.mutate()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white border-gray-200 shadow-xl">
        <CardHeader className="flex flex-row items-center justify-between border-b border-gray-200">
          <CardTitle className="text-xl font-bold text-gray-900">
            Send email to {lead.Name ?? lead.Email}
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
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-3">B2C lead (post comment)</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Name:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Name ?? '—'}</span>
              </div>
              <div>
                <span className="text-gray-600">Email:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Email}</span>
              </div>
              <div>
                <span className="text-gray-600">Source:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Source ?? '—'}</span>
              </div>
              <div>
                <span className="text-gray-600">Campaign:</span>
                <span className="ml-2 font-medium text-gray-900">{lead.Campaign ?? '—'}</span>
              </div>
              <div>
                <span className="text-gray-600">Stage:</span>
                <Badge variant="outline" className="ml-2">
                  {lead.Stage ?? '—'}
                </Badge>
              </div>
              {lead.Follow_Up_Count != null && Number(lead.Follow_Up_Count) > 0 && (
                <div>
                  <span className="text-gray-600">Follow-ups sent:</span>
                  <span className="ml-2 font-medium text-gray-900">{lead.Follow_Up_Count}</span>
                </div>
              )}
              {lead.Last_Activity_Date && (
                <div>
                  <span className="text-gray-600">Last activity:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {formatDate(lead.Last_Activity_Date)}
                  </span>
                </div>
              )}
              {lead.Next_Followup_Date && (
                <div>
                  <span className="text-gray-600">Next follow-up:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {formatDate(lead.Next_Followup_Date)}
                  </span>
                </div>
              )}
            </div>
            {lead.Notes && (
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Notes (post context):</span>
                <p className="text-sm text-gray-600 mt-1">{lead.Notes}</p>
              </div>
            )}
          </div>
          <p className="text-sm text-gray-600">
            This will create a draft email referencing the post/campaign they commented on. The draft will use your company brand context. After you approve it, the email can be sent from the Drafts page.
          </p>
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
                  Create draft
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
