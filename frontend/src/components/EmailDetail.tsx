import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { formatDate, getPriorityColor } from '../lib/utils'
import { Mail, Clock, User, Building2, AlertCircle, MessageSquare } from 'lucide-react'

interface EmailDetailProps {
  email: {
    id: string
    subject: string
    from_email: string
    to_email: string
    body: string
    priority_score: string | null
    executive_summary: string | null
    function: string | null
    intent: string | null
    urgency: string | null
    impact: string | null
    confidence: string | null
    recommended_action: string | null
    thread_id: string | null
    thread_history?: Array<{
      subject: string
      body: string
      from_email: string
      created_at: string | null
      was_reply: boolean
    }>
    thread_count?: number
    created_at: string
  }
  companyName?: string
}

export default function EmailDetail({ email, companyName }: EmailDetailProps) {
  return (
    <div className="space-y-4">
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Original Email</CardTitle>
          <CardDescription>Full email context for review</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Priority Score */}
          {email.priority_score && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Priority Score:</span>
              <div
                className={`px-3 py-1 rounded-lg text-white font-bold ${getPriorityColor(
                  email.priority_score
                )}`}
              >
                {email.priority_score}
              </div>
            </div>
          )}

          {/* Executive Summary */}
          {email.executive_summary && (
            <div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">Executive Summary</h4>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md">
                {email.executive_summary}
              </p>
            </div>
          )}

          {/* Email Metadata */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <Mail className="w-4 h-4" />
              <span className="font-medium">From:</span>
              <span>{email.from_email}</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Mail className="w-4 h-4" />
              <span className="font-medium">To:</span>
              <span>{email.to_email}</span>
            </div>
            {companyName && (
              <div className="flex items-center gap-2 text-gray-600">
                <Building2 className="w-4 h-4" />
                <span className="font-medium">Company:</span>
                <span>{companyName}</span>
              </div>
            )}
            <div className="flex items-center gap-2 text-gray-600">
              <Clock className="w-4 h-4" />
              <span className="font-medium">Date:</span>
              <span>{formatDate(email.created_at)}</span>
            </div>
          </div>

          {/* Subject */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-1">Subject</h4>
            <p className="text-sm text-gray-700">{email.subject}</p>
          </div>

          {/* Body */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-1">Body</h4>
            <div className="text-sm text-gray-700 bg-gray-50 p-4 rounded-md whitespace-pre-wrap max-h-64 overflow-y-auto break-words">
              {email.body}
            </div>
          </div>

          {/* Thread Context */}
          {email.thread_id && (
            <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-gray-600">
                <MessageSquare className="w-4 h-4" />
                <span className="font-medium">Thread Information:</span>
                <Badge variant="outline" className="border-blue-300 text-blue-700">
                  {email.thread_count || 0} previous {email.thread_count === 1 ? 'email' : 'emails'}
                </Badge>
                <span className="text-xs text-gray-500">
                  Thread ID: {email.thread_id.substring(0, 20)}...
                </span>
              </div>
              
              {/* Thread History */}
              {email.thread_history && email.thread_history.length > 0 && (
                <div className="mt-3 border-t pt-3">
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">Conversation History</h4>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {email.thread_history.map((prevEmail, index) => (
                      <div
                        key={index}
                        className="bg-gray-50 p-3 rounded-md border border-gray-200"
                      >
                        <div className="flex items-start justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <Mail className="w-3 h-3 text-gray-500" />
                            <span className="text-xs font-medium text-gray-700">
                              {prevEmail.from_email}
                            </span>
                            {prevEmail.was_reply && (
                              <Badge variant="outline" className="text-xs border-gray-300 text-gray-600">
                                Reply
                              </Badge>
                            )}
                          </div>
                          {prevEmail.created_at && (
                            <span className="text-xs text-gray-500">
                              {formatDate(prevEmail.created_at)}
                            </span>
                          )}
                        </div>
                        <p className="text-xs font-semibold text-gray-900 mb-1">
                          {prevEmail.subject}
                        </p>
                        <p className="text-xs text-gray-600 line-clamp-2">
                          {prevEmail.body}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Classification Metadata */}
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Classification</CardTitle>
          <CardDescription>AI classification metadata</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            {email.function && (
              <div>
                <span className="text-xs font-medium text-gray-500">Function</span>
                <Badge variant="outline" className="mt-1 block w-fit border-gray-300 text-gray-700">
                  {email.function}
                </Badge>
              </div>
            )}
            {email.intent && (
              <div>
                <span className="text-xs font-medium text-gray-500">Intent</span>
                <Badge variant="outline" className="mt-1 block w-fit border-gray-300 text-gray-700">
                  {email.intent}
                </Badge>
              </div>
            )}
            {email.urgency && (
              <div>
                <span className="text-xs font-medium text-gray-500">Urgency</span>
                <Badge variant="outline" className="mt-1 block w-fit border-gray-300 text-gray-700">
                  {email.urgency}
                </Badge>
              </div>
            )}
            {email.impact && (
              <div>
                <span className="text-xs font-medium text-gray-500">Impact</span>
                <Badge variant="outline" className="mt-1 block w-fit border-gray-300 text-gray-700">
                  {email.impact}
                </Badge>
              </div>
            )}
            {email.confidence && (
              <div>
                <span className="text-xs font-medium text-gray-500">Confidence</span>
                <Badge variant="outline" className="mt-1 block w-fit border-gray-300 text-gray-700">
                  {email.confidence}
                </Badge>
              </div>
            )}
            {email.recommended_action && (
              <div className="col-span-2">
                <span className="text-xs font-medium text-gray-500">Recommended Action</span>
                <Badge
                  variant="outline"
                  className="mt-1 block w-fit border-gray-400 text-gray-700"
                >
                  {email.recommended_action}
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

