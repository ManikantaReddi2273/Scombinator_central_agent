import { useQuery } from '@tanstack/react-query'
import { emailsAPI, draftsAPI, companiesAPI } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { TrendingUp, FileText, Building2, Mail, Plus } from 'lucide-react'
import { formatDate } from '../lib/utils'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { useState } from 'react'
import AddCompanyModal from '../components/AddCompanyModal'

export default function Dashboard() {
  const [isAddCompanyOpen, setIsAddCompanyOpen] = useState(false)
  const { data: priorityQueue } = useQuery({
    queryKey: ['priority-queue'],
    queryFn: () => emailsAPI.getPriorityQueue(5).then((res) => res.data),
  })

  const { data: pendingDrafts } = useQuery({
    queryKey: ['drafts-pending'],
    queryFn: () => draftsAPI.getPending(5).then((res) => res.data),
  })

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesAPI.list().then((res) => res.data),
  })

  const { data: emails } = useQuery({
    queryKey: ['emails'],
    queryFn: () => emailsAPI.list({ limit: 5 }).then((res) => res.data),
  })

  const stats = [
    {
      title: 'Companies',
      value: companies?.length || 0,
      icon: Building2,
      color: 'text-gray-600',
      bg: 'bg-gray-200',
    },
    {
      title: 'Pending Drafts',
      value: pendingDrafts?.length || 0,
      icon: FileText,
      color: 'text-yellow-500',
      bg: 'bg-yellow-500/10',
    },
    {
      title: 'High Priority',
      value: priorityQueue?.filter((e: any) => parseInt(e.priority_score) >= 80).length || 0,
      icon: TrendingUp,
      color: 'text-red-500',
      bg: 'bg-red-500/10',
    },
    {
      title: 'Total Emails',
      value: emails?.length || 0,
      icon: Mail,
      color: 'text-purple-500',
      bg: 'bg-purple-500/10',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
          <p className="text-gray-600">Overview of your multi-company operations</p>
        </div>
        <Button
          onClick={() => setIsAddCompanyOpen(true)}
          className="bg-gradient-to-r from-gray-300 to-gray-400 hover:from-gray-400 hover:to-gray-500 text-gray-900 shadow-md"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Company
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title} className="bg-white border-gray-200 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">{stat.title}</p>
                    <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                  </div>
                  <div className={`${stat.bg} p-3 rounded-lg`}>
                    <Icon className={`w-6 h-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Queue */}
        <Card className="bg-white border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-gray-900">Priority Queue</CardTitle>
                <CardDescription>Top priority items across all companies</CardDescription>
              </div>
              <Link to="/priority-queue">
                <Button variant="ghost" size="sm">View All</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {priorityQueue?.length > 0 ? (
                priorityQueue.map((item: any) => (
                  <div
                    key={item.email_id}
                    className="p-4 rounded-lg bg-[#EAEFEF] border border-gray-200 hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 text-sm">{item.subject}</p>
                        <p className="text-xs text-gray-600 mt-1">{item.company_name}</p>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs font-bold text-white ${
                        parseInt(item.priority_score) >= 80 ? 'bg-red-500' :
                        parseInt(item.priority_score) >= 60 ? 'bg-orange-500' :
                        'bg-yellow-500'
                      }`}>
                        {item.priority_score}
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{item.executive_summary}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">No priority items</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pending Drafts */}
        <Card className="bg-white border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-gray-900">Pending Drafts</CardTitle>
                <CardDescription>Awaiting your approval</CardDescription>
              </div>
              <Link to="/drafts">
                <Button variant="ghost" size="sm">View All</Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingDrafts?.length > 0 ? (
                pendingDrafts.map((draft: any) => (
                  <div
                    key={draft.id}
                    className="p-4 rounded-lg bg-[#EAEFEF] border border-gray-200 hover:border-gray-300 transition-colors"
                  >
                    <p className="font-medium text-gray-900 text-sm mb-1">{draft.subject}</p>
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2">{draft.body}</p>
                    <p className="text-xs text-gray-500">{formatDate(draft.created_at)}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">No pending drafts</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

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

