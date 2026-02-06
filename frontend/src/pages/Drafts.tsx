import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { draftsAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { formatDate, getStatusColor } from '../lib/utils'
import { Check, X, Eye, Edit } from 'lucide-react'
import { useState } from 'react'

export default function Drafts() {
  const [selectedDraft, setSelectedDraft] = useState<string | null>(null)
  const [editedBody, setEditedBody] = useState('')
  const queryClient = useQueryClient()

  const { data: drafts, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => draftsAPI.list().then((res) => res.data),
  })

  const { data: selectedDraftData } = useQuery({
    queryKey: ['draft', selectedDraft],
    queryFn: () => draftsAPI.get(selectedDraft!).then((res) => res.data),
    enabled: !!selectedDraft,
  })

  const approveMutation = useMutation({
    mutationFn: (data: { id: string; edited_body?: string }) =>
      draftsAPI.approve(data.id, { edited_body: data.edited_body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['draft', selectedDraft] })
      setSelectedDraft(null)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: (id: string) => draftsAPI.reject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setSelectedDraft(null)
    },
  })

  const pendingDrafts = drafts?.filter((d: any) => d.status === 'pending') || []
  const approvedDrafts = drafts?.filter((d: any) => d.status === 'approved') || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Draft Management</h1>
        <p className="text-gray-600">Review, edit, and approve email drafts</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Drafts List */}
        <div className="lg:col-span-2 space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Pending Drafts</h2>
            <div className="space-y-3">
              {isLoading ? (
                <div className="text-center py-8 text-gray-500">Loading...</div>
              ) : pendingDrafts.length > 0 ? (
                pendingDrafts.map((draft: any) => (
                  <Card
                    key={draft.id}
                    className={`bg-white border-gray-200 cursor-pointer transition-colors shadow-sm ${
                      selectedDraft === draft.id
                        ? 'border-gray-400 ring-2 ring-gray-400/20'
                        : 'hover:border-gray-300'
                    }`}
                    onClick={() => {
                      setSelectedDraft(draft.id)
                      setEditedBody(draft.body)
                    }}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-1">{draft.subject}</h3>
                          <p className="text-sm text-gray-600 line-clamp-2 mb-2">{draft.body}</p>
                          <div className="flex items-center gap-2">
                            <Badge
                              className={`${getStatusColor(draft.status)} text-white text-xs`}
                            >
                              {draft.status}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {formatDate(draft.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card className="bg-white border-gray-200">
                  <CardContent className="p-12 text-center">
                    <p className="text-gray-500">No pending drafts</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>

          {approvedDrafts.length > 0 && (
            <div className="mt-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Approved Drafts</h2>
              <div className="space-y-3">
                {approvedDrafts.map((draft: any) => (
                  <Card
                    key={draft.id}
                    className="bg-white border-gray-200 opacity-75"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900 mb-1">{draft.subject}</h3>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className="bg-green-500 text-white text-xs">
                              {draft.status}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              {formatDate(draft.created_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Draft Editor */}
        <div className="lg:col-span-1">
          {selectedDraftData ? (
            <Card className="bg-white border-gray-200 sticky top-20 shadow-lg">
              <CardHeader>
                <CardTitle className="text-gray-900">Edit & Approve</CardTitle>
                <CardDescription>Review and edit the draft before approval</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Subject
                  </label>
                  <input
                    type="text"
                    value={selectedDraftData.subject}
                    readOnly
                    className="w-full px-3 py-2 rounded-md bg-[#EAEFEF] border border-gray-300 text-gray-900 text-sm"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Body
                  </label>
                  <textarea
                    value={editedBody}
                    onChange={(e) => setEditedBody(e.target.value)}
                    rows={12}
                    className="w-full px-3 py-2 rounded-md bg-white border border-gray-300 text-gray-900 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-gray-400"
                  />
                </div>
                <div className="flex gap-2">
                  <Button
                    className="flex-1 bg-green-600 hover:bg-green-700"
                    onClick={() =>
                      approveMutation.mutate({
                        id: selectedDraftData.id,
                        edited_body: editedBody !== selectedDraftData.body ? editedBody : undefined,
                      })
                    }
                    disabled={approveMutation.isPending}
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={() => rejectMutation.mutate(selectedDraftData.id)}
                    disabled={rejectMutation.isPending}
                  >
                    <X className="w-4 h-4 mr-2" />
                    Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-white border-gray-200">
              <CardContent className="p-12 text-center">
                <Eye className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">Select a draft to review</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

