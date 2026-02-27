import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { X, Sparkles, Loader2, Check, RotateCcw } from 'lucide-react'
import { draftsAPI } from '../lib/api'

interface DraftAIEditModalProps {
  isOpen: boolean
  onClose: () => void
  draftId: string
  currentSubject: string
  currentBody: string
  onKeepChanges: (subject: string, body: string) => void
}

type Step = 'instruction' | 'preview'

export default function DraftAIEditModal({
  isOpen,
  onClose,
  draftId,
  currentSubject,
  currentBody,
  onKeepChanges,
}: DraftAIEditModalProps) {
  const [step, setStep] = useState<Step>('instruction')
  const [instruction, setInstruction] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [preview, setPreview] = useState<{ subject: string; body: string } | null>(null)

  useEffect(() => {
    if (!isOpen) {
      setStep('instruction')
      setInstruction('')
      setError(null)
      setPreview(null)
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = instruction.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await draftsAPI.aiEdit(draftId, {
        instruction: trimmed,
        current_subject: currentSubject,
        current_body: currentBody,
      })
      setPreview({ subject: data.subject, body: data.body })
      setStep('preview')
    } catch (err: any) {
      const detail = err.response?.data?.detail
      let msg = 'AI edit failed. Please try again or edit manually.'
      if (typeof detail === 'string') {
        msg = detail
      } else if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0]
        msg = typeof first === 'string' ? first : (first?.msg || first?.message || msg)
      } else if (detail && typeof detail === 'object' && (detail.msg || detail.message)) {
        msg = detail.msg || detail.message
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleKeepChanges = () => {
    if (preview) {
      onKeepChanges(preview.subject, preview.body)
    }
    onClose()
  }

  const handleDiscard = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] flex flex-col bg-white border-gray-200 shadow-2xl">
        <CardHeader className="relative shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
            onClick={onClose}
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </Button>
          <div className="flex items-center gap-3 pr-10">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <CardTitle className="text-gray-900">Edit with AI</CardTitle>
              <CardDescription>
                {step === 'instruction'
                  ? 'Describe how you want to change the draft (tone, length, audience, etc.)'
                  : 'Review the AI-generated changes below'}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col min-h-0 flex-1 overflow-hidden">
          {step === 'instruction' ? (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}
              <div>
                <label htmlFor="ai-instruction" className="text-sm font-medium text-gray-700 block mb-2">
                  Instruction
                </label>
                <textarea
                  id="ai-instruction"
                  placeholder="e.g. Change the tone to more formal / Make it shorter and more direct / Emphasize security and compliance / Fix grammar and improve clarity"
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  rows={4}
                  maxLength={500}
                  className="w-full px-3 py-2 rounded-md border border-gray-300 bg-white text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y disabled:opacity-60"
                  disabled={loading}
                  autoFocus
                />
                <p className="text-xs text-gray-500 mt-1">{instruction.length}/500</p>
              </div>
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={onClose}
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  disabled={loading || !instruction.trim()}
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Editing draft...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Edit with AI
                    </>
                  )}
                </Button>
              </div>
            </form>
          ) : (
            <div className="flex flex-col gap-4 min-h-0 overflow-hidden">
              <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-800">
                AI-generated modification – review below. Choose Keep Changes to apply, or Discard to leave the draft unchanged.
              </div>
              {preview && (
                <div className="flex flex-col gap-3 min-h-0 overflow-hidden flex-1">
                  <div>
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Subject</label>
                    <p className="mt-1 px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-gray-900 text-sm break-words">
                      {preview.subject}
                    </p>
                  </div>
                  <div className="flex-1 min-h-0 flex flex-col">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Body</label>
                    <div
                      className="mt-1 flex-1 min-h-[200px] px-3 py-2 rounded-md bg-gray-50 border border-gray-200 text-gray-900 text-sm overflow-y-auto whitespace-pre-wrap break-words"
                      style={{ wordWrap: 'break-word' }}
                    >
                      {preview.body}
                    </div>
                  </div>
                </div>
              )}
              <div className="flex gap-3 pt-2 shrink-0">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={handleDiscard}
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Discard
                </Button>
                <Button
                  type="button"
                  className="flex-1 bg-green-600 hover:bg-green-700"
                  onClick={handleKeepChanges}
                >
                  <Check className="w-4 h-4 mr-2" />
                  Keep Changes
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
