import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import {
  CheckSquare, Plus, Filter, Grid, List, X, Edit2, Trash2,
  User, Calendar, AlertCircle, Star, Clock, Download, Phone,
  TrendingUp, Flag, ExternalLink, UserPlus, MoreVertical, FileText,
  MessageSquare, Tag, PlayCircle
} from 'lucide-react'
import { format, isPast, isToday, isTomorrow, addDays } from 'date-fns'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './ui/table'
import { Skeleton } from './ui/skeleton'
import ExportDialog from './ExportDialog'
import api from '../api'
import toast from 'react-hot-toast'
import { formatDuration, formatPhoneNumber } from '@/lib/utils'

// Helper functions
const getDueDateStatus = (dueDate) => {
  if (!dueDate) return null
  const date = new Date(dueDate)
  if (isPast(date) && !isToday(date)) return 'overdue'
  if (isToday(date)) return 'today'
  if (isTomorrow(date)) return 'tomorrow'
  return 'upcoming'
}

const getDueDateColor = (status) => {
  switch (status) {
    case 'overdue': return 'destructive'
    case 'today': return 'warning'
    case 'tomorrow': return 'default'
    default: return 'secondary'
  }
}

const getDueDateText = (dueDate) => {
  if (!dueDate) return null
  const status = getDueDateStatus(dueDate)
  if (status === 'overdue') return `Overdue: ${format(new Date(dueDate), 'MMM d')}`
  if (status === 'today') return 'Due Today'
  if (status === 'tomorrow') return 'Due Tomorrow'
  return `Due ${format(new Date(dueDate), 'MMM d, yyyy')}`
}

const getSentimentColor = (sentiment) => {
  switch (sentiment) {
    case 'positive': return 'success'
    case 'negative': return 'destructive'
    default: return 'secondary'
  }
}

// Call Detail Modal Component
function CallDetailModal({ callId, open, onClose }) {
  const [isLoading, setIsLoading] = useState(false)
  const [callData, setCallData] = useState(null)

  useMemo(() => {
    if (open && callId) {
      setIsLoading(true)
      api.get(`/calls/${callId}`)
        .then(response => {
          setCallData(response.data)
          setIsLoading(false)
        })
        .catch(error => {
          console.error('Failed to fetch call details:', error)
          toast.error('Failed to load call details')
          setIsLoading(false)
        })
    } else {
      setCallData(null)
    }
  }, [open, callId])

  if (!open) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5 text-primary" />
            Related Call Details
          </DialogTitle>
          {callData && (
            <DialogDescription>
              {format(new Date(callData.start_time), 'MMMM d, yyyy h:mm a')}
            </DialogDescription>
          )}
        </DialogHeader>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-sm text-muted-foreground">Loading call details...</div>
          </div>
        ) : callData ? (
          <div className="space-y-6">
            {/* Call Metadata */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Caller</p>
                <p className="text-sm font-semibold">{callData.caller_name || 'Unknown'}</p>
                <p className="text-xs text-muted-foreground">{formatPhoneNumber(callData.caller_number)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Duration</p>
                <p className="text-sm font-semibold">{formatDuration(callData.duration_seconds)}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Direction</p>
                <p className="text-sm font-semibold capitalize">{callData.direction || 'N/A'}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Recording</p>
                <Badge variant={callData.has_recording ? 'success' : 'secondary'}>
                  {callData.has_recording ? 'Available' : 'Not Available'}
                </Badge>
              </div>
            </div>

            {/* Sentiment & Urgency */}
            {(callData.summary?.sentiment || callData.sentiment) && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Sentiment</p>
                  <Badge variant={getSentimentColor(callData.summary?.sentiment || callData.sentiment)}>
                    {callData.summary?.sentiment || callData.sentiment}
                  </Badge>
                </div>
                {(callData.summary?.urgency_score || callData.urgency_score) && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground mb-2">Urgency</p>
                    <div className="flex items-center gap-2">
                      <Badge variant={(callData.summary?.urgency_score || callData.urgency_score) >= 4 ? 'destructive' : 'secondary'}>
                        {callData.summary?.urgency_score || callData.urgency_score}/5
                      </Badge>
                      {(callData.summary?.urgency_score || callData.urgency_score) >= 4 && <AlertCircle className="h-4 w-4 text-red-500" />}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Summary */}
            {callData.summary?.summary && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  AI Summary
                </h4>
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm text-gray-700">{callData.summary.summary}</p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Key Topics */}
            {callData.summary?.key_topics && callData.summary.key_topics.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Key Topics</h4>
                <div className="flex flex-wrap gap-2">
                  {callData.summary.key_topics.map((topic, idx) => (
                    <Badge key={idx} variant="outline">{topic}</Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Transcript */}
            {callData.summary?.transcript && (
              <div>
                <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Full Transcript
                </h4>
                <Card>
                  <CardContent className="p-4 max-h-[300px] overflow-y-auto">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{callData.summary.transcript}</p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Recording URL */}
            {callData.recording_url && (
              <div>
                <Button variant="outline" className="w-full" asChild>
                  <a href={callData.recording_url} target="_blank" rel="noopener noreferrer">
                    <PlayCircle className="mr-2 h-4 w-4" />
                    Play Recording
                  </a>
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-sm text-muted-foreground">
            No call data available
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

// Action Item Detail Modal Component
function ActionItemDetailModal({ item, open, onClose, onEdit, onDelete, onComplete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [showCallModal, setShowCallModal] = useState(false)
  const [editedDescription, setEditedDescription] = useState(item?.description || '')
  const dueDateStatus = getDueDateStatus(item?.due_date)

  const handleSave = () => {
    if (editedDescription !== item.description) {
      onEdit(item.id, { description: editedDescription })
    }
    setIsEditing(false)
  }

  if (!item) return null

  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckSquare className="h-5 w-5 text-primary" />
              Action Item Details
            </DialogTitle>
            <DialogDescription>
              Created {format(new Date(item.created_at), 'MMMM d, yyyy h:mm a')}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6">
            {/* Overdue Alert */}
            {dueDateStatus === 'overdue' && (
              <div className="flex items-center gap-2 text-red-600 bg-red-100 px-4 py-3 rounded-lg">
                <AlertCircle className="h-5 w-5" />
                <div>
                  <p className="font-semibold">This action item is overdue!</p>
                  <p className="text-sm">Due date was {format(new Date(item.due_date), 'MMMM d, yyyy')}</p>
                </div>
              </div>
            )}

            {/* Description */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-semibold">Description</label>
                {!isEditing && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsEditing(true)}
                    className="h-7"
                  >
                    <Edit2 className="h-3 w-3 mr-1" />
                    Edit
                  </Button>
                )}
              </div>
              {isEditing ? (
                <div className="space-y-2">
                  <Input
                    value={editedDescription}
                    onChange={(e) => setEditedDescription(e.target.value)}
                    className="text-sm"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSave}>Save</Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditedDescription(item.description)
                        setIsEditing(false)
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <Card>
                  <CardContent className="p-4">
                    <p className="text-sm">{item.description}</p>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-semibold text-muted-foreground">Status</label>
                <div className="mt-1">
                  <Badge
                    variant={
                      item.status === 'completed' ? 'success' :
                      item.status === 'in_progress' ? 'default' :
                      'secondary'
                    }
                    className="text-sm"
                  >
                    {item.status || 'pending'}
                  </Badge>
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold text-muted-foreground">Priority</label>
                <div className="mt-1 flex items-center gap-1">
                  {Array(5).fill(0).map((_, i) => (
                    <Star
                      key={i}
                      className={`h-4 w-4 ${
                        i < item.priority
                          ? 'fill-yellow-400 text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                  <span className="text-sm text-muted-foreground ml-2">
                    ({item.priority}/5)
                  </span>
                </div>
              </div>

              <div>
                <label className="text-sm font-semibold text-muted-foreground">Assigned To</label>
                <p className="text-sm mt-1 flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  {item.assigned_to || <span className="text-muted-foreground">Unassigned</span>}
                </p>
              </div>

              <div>
                <label className="text-sm font-semibold text-muted-foreground">Due Date</label>
                <p className="text-sm mt-1 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  {item.due_date ? (
                    <Badge variant={getDueDateColor(dueDateStatus)}>
                      {getDueDateText(item.due_date)}
                    </Badge>
                  ) : (
                    <span className="text-muted-foreground">No due date</span>
                  )}
                </p>
              </div>
            </div>

            {/* Related Call Section */}
            {item.call_info && (
              <div>
                <label className="text-sm font-semibold mb-2 block">Related Call</label>
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-blue-600" />
                          <span className="font-semibold text-blue-900">
                            {item.call_info.caller}
                          </span>
                        </div>
                        <div className="text-sm text-blue-700">
                          <p>Call ID: #{item.call_id}</p>
                          <p>Direction: {item.call_info.direction}</p>
                          <p>Time: {format(new Date(item.call_info.start_time), 'MMM d, yyyy h:mm a')}</p>
                        </div>
                      </div>
                      <Button
                        onClick={() => setShowCallModal(true)}
                        variant="outline"
                        size="sm"
                        className="shrink-0"
                      >
                        <PlayCircle className="h-4 w-4 mr-1" />
                        View Call
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Timestamps */}
            <div className="grid grid-cols-2 gap-4 pt-4 border-t">
              <div>
                <label className="text-xs font-semibold text-muted-foreground">Created</label>
                <p className="text-xs text-muted-foreground mt-1">
                  {format(new Date(item.created_at), 'MMM d, yyyy h:mm a')}
                </p>
              </div>
              {item.completed_at && (
                <div>
                  <label className="text-xs font-semibold text-muted-foreground">Completed</label>
                  <p className="text-xs text-muted-foreground mt-1">
                    {format(new Date(item.completed_at), 'MMM d, yyyy h:mm a')}
                  </p>
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="flex gap-2">
            {item.status !== 'completed' && (
              <Button
                onClick={() => {
                  onComplete(item.id)
                  onClose()
                }}
                className="flex-1"
              >
                <CheckSquare className="h-4 w-4 mr-2" />
                Mark Complete
              </Button>
            )}
            <Button
              onClick={() => {
                if (confirm('Are you sure you want to delete this action item?')) {
                  onDelete(item.id)
                  onClose()
                }
              }}
              variant="destructive"
              className="flex-1"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Call Detail Modal */}
      <CallDetailModal
        callId={item.call_id}
        open={showCallModal}
        onClose={() => setShowCallModal(false)}
      />
    </>
  )
}

// Action Item Card Component
function ActionItemCard({ item, index, onEdit, onDelete, onViewDetails }) {
  const queryClient = useQueryClient()
  const dueDateStatus = getDueDateStatus(item.due_date)

  const completeMutation = useMutation({
    mutationFn: async (id) => {
      const response = await api.post(`/actions/${id}/complete`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      queryClient.invalidateQueries(['actionItemsStats'])
      toast.success('Action completed! ✓')
    },
  })

  const assignToMeMutation = useMutation({
    mutationFn: async (id) => {
      const response = await api.patch(`/actions/${id}`, { assigned_to: 'Me' })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      toast.success('Assigned to you')
    },
  })

  const snoozeMutation = useMutation({
    mutationFn: async ({ id, days }) => {
      const newDate = addDays(new Date(), days).toISOString()
      const response = await api.patch(`/actions/${id}`, { due_date: newDate })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      toast.success('Snoozed')
    },
  })

  const getPriorityStars = (priority) => {
    return Array(5).fill(0).map((_, i) => (
      <Star
        key={i}
        className={`h-3 w-3 ${i < priority ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ))
  }

  return (
    <Draggable draggableId={item.id.toString()} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`mb-3 ${snapshot.isDragging ? 'opacity-50' : ''}`}
        >
          <Card
            className={`hover:shadow-md transition-shadow cursor-pointer ${snapshot.isDragging ? 'shadow-lg' : ''} ${dueDateStatus === 'overdue' ? 'border-red-300 bg-red-50/30' : ''}`}
            onClick={() => onViewDetails(item)}
          >
            <CardContent className="p-4">
              <div className="space-y-3">
                {/* Overdue Banner */}
                {dueDateStatus === 'overdue' && (
                  <div className="flex items-center gap-2 text-red-600 text-xs font-medium bg-red-100 px-2 py-1 rounded">
                    <AlertCircle className="h-3 w-3" />
                    OVERDUE
                  </div>
                )}

                {/* Header */}
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 break-words">
                      {item.description}
                    </p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        assignToMeMutation.mutate(item.id)
                      }}>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Assign to Me
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        snoozeMutation.mutate({ id: item.id, days: 1 })
                      }}>
                        <Clock className="h-4 w-4 mr-2" />
                        Snooze 1 day
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => {
                        e.stopPropagation()
                        snoozeMutation.mutate({ id: item.id, days: 7 })
                      }}>
                        <Calendar className="h-4 w-4 mr-2" />
                        Snooze 1 week
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation()
                          if (confirm('Are you sure you want to delete this action item?')) {
                            onDelete(item.id)
                          }
                        }}
                        className="text-red-600"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Priority & Due Date */}
                <div className="flex items-center gap-3 flex-wrap">
                  {item.priority && (
                    <div className="flex items-center gap-1">
                      <Flag className="h-3 w-3 text-muted-foreground" />
                      {getPriorityStars(item.priority)}
                    </div>
                  )}
                  {item.due_date && (
                    <Badge variant={getDueDateColor(dueDateStatus)} className="text-xs">
                      {getDueDateText(item.due_date)}
                    </Badge>
                  )}
                </div>

                {/* Assignee */}
                {item.assigned_to && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    <span>{item.assigned_to}</span>
                  </div>
                )}

                {/* Call Context */}
                {item.call_info && (
                  <div className="flex items-center gap-2 text-xs bg-blue-50 px-2 py-1.5 rounded">
                    <Phone className="h-3 w-3 text-blue-600" />
                    <span className="text-blue-900">
                      From {item.call_info.caller} • {format(new Date(item.call_info.start_time), 'MMM d, h:mm a')}
                    </span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2 border-t">
                  {item.status !== 'completed' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        completeMutation.mutate(item.id)
                      }}
                      className="text-xs h-7 flex-1"
                      disabled={completeMutation.isLoading}
                    >
                      <CheckSquare className="h-3 w-3 mr-1" />
                      Mark Complete
                    </Button>
                  )}
                  {item.status === 'completed' && (
                    <Badge variant="success" className="flex-1 justify-center">
                      <CheckSquare className="h-3 w-3 mr-1" />
                      Completed
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </Draggable>
  )
}

// Kanban Column Component
function KanbanColumn({ title, status, items, onEdit, onDelete, onViewDetails }) {
  const getBgColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-50'
      case 'in_progress': return 'bg-blue-50'
      case 'completed': return 'bg-green-50'
      default: return 'bg-gray-50'
    }
  }

  const getHeaderColor = (status) => {
    switch (status) {
      case 'pending': return 'text-yellow-700'
      case 'in_progress': return 'text-blue-700'
      case 'completed': return 'text-green-700'
      default: return 'text-gray-700'
    }
  }

  return (
    <div className="flex-1 min-w-[300px]">
      <div className={`rounded-lg p-4 ${getBgColor(status)}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`font-semibold ${getHeaderColor(status)}`}>{title}</h3>
          <Badge variant="secondary">{items.length}</Badge>
        </div>

        <Droppable droppableId={status}>
          {(provided, snapshot) => (
            <div
              ref={provided.innerRef}
              {...provided.droppableProps}
              className={`min-h-[500px] ${snapshot.isDraggingOver ? 'bg-blue-100/50 rounded-lg' : ''}`}
            >
              {items.map((item, index) => (
                <ActionItemCard
                  key={item.id}
                  item={item}
                  index={index}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  onViewDetails={onViewDetails}
                />
              ))}
              {provided.placeholder}
              {items.length === 0 && (
                <div className="text-center py-8 text-sm text-muted-foreground">
                  No items
                </div>
              )}
            </div>
          )}
        </Droppable>
      </div>
    </div>
  )
}

// Main Component
export default function ActionItems() {
  const [viewMode, setViewMode] = useState('kanban') // 'kanban' or 'table'
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [selectedItem, setSelectedItem] = useState(null)
  const [showDetailModal, setShowDetailModal] = useState(false)

  const queryClient = useQueryClient()

  // Fetch action items
  const { data: actionItemsData, isLoading } = useQuery({
    queryKey: ['actionItems', { status: statusFilter === 'all' ? undefined : statusFilter }],
    queryFn: async () => {
      const params = {}
      if (statusFilter !== 'all') params.status = statusFilter
      const response = await api.get('/actions', { params })
      return response.data
    },
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['actionItemsStats'],
    queryFn: async () => {
      const response = await api.get('/actions/stats')
      return response.data
    },
  })

  const actionItems = actionItemsData?.action_items || []
  const stats = statsData || { pending: 0, in_progress: 0, completed: 0, total: 0 }

  // Group items by status
  const itemsByStatus = useMemo(() => ({
    pending: actionItems.filter(item => item.status === 'pending' || !item.status),
    in_progress: actionItems.filter(item => item.status === 'in_progress'),
    completed: actionItems.filter(item => item.status === 'completed'),
  }), [actionItems])

  // Count overdue items
  const overdueCount = useMemo(() => {
    return actionItems.filter(item =>
      item.status !== 'completed' &&
      getDueDateStatus(item.due_date) === 'overdue'
    ).length
  }, [actionItems])

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await api.patch(`/actions/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      queryClient.invalidateQueries(['actionItemsStats'])
      toast.success('Action item updated')
    },
    onError: () => {
      toast.error('Failed to update action item')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      await api.delete(`/actions/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      queryClient.invalidateQueries(['actionItemsStats'])
      toast.success('Action item deleted')
    },
    onError: () => {
      toast.error('Failed to delete action item')
    },
  })

  // Complete mutation
  const completeMutation = useMutation({
    mutationFn: async (id) => {
      const response = await api.post(`/actions/${id}/complete`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['actionItems'])
      queryClient.invalidateQueries(['actionItemsStats'])
      toast.success('Action completed!')
    },
  })

  // Handle drag end
  const handleDragEnd = (result) => {
    if (!result.destination) return

    const itemId = parseInt(result.draggableId)
    const newStatus = result.destination.droppableId

    updateMutation.mutate({
      id: itemId,
      data: { status: newStatus }
    })
  }

  const handleEdit = (id, data) => {
    updateMutation.mutate({ id, data })
  }

  const handleDelete = (id) => {
    deleteMutation.mutate(id)
  }

  const handleViewDetails = (item) => {
    setSelectedItem(item)
    setShowDetailModal(true)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading action items...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Action Items</h2>
          <p className="mt-1 text-sm text-gray-500">
            Track and manage {stats.total} tasks from your calls • Click any item to view details
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => setShowExportDialog(true)}
            variant="outline"
            className="gap-2"
            disabled={!actionItems || actionItems.length === 0}
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* View Toggle */}
            <div className="flex items-center gap-2">
              <Button
                variant={viewMode === 'kanban' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('kanban')}
                className="gap-2"
              >
                <Grid className="h-4 w-4" />
                Board
              </Button>
              <Button
                variant={viewMode === 'table' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('table')}
                className="gap-2"
              >
                <List className="h-4 w-4" />
                List
              </Button>
            </div>

            {/* Filters */}
            {viewMode === 'table' && (
              <>
                <div className="flex-1" />
                <div className="flex items-center gap-3">
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>

                  <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                    <SelectTrigger className="w-[150px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Priority</SelectItem>
                      <SelectItem value="5">Critical (5)</SelectItem>
                      <SelectItem value="4">High (4)</SelectItem>
                      <SelectItem value="3">Medium (3)</SelectItem>
                      <SelectItem value="1-2">Low (1-2)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Pending</p>
                <p className="text-2xl font-bold mt-1">{stats.pending}</p>
              </div>
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">In Progress</p>
                <p className="text-2xl font-bold mt-1">{stats.in_progress}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold mt-1">{stats.completed}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckSquare className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className={overdueCount > 0 ? 'border-red-300 bg-red-50' : ''}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Overdue</p>
                <p className={`text-2xl font-bold mt-1 ${overdueCount > 0 ? 'text-red-600' : ''}`}>
                  {overdueCount}
                </p>
              </div>
              <div className={`p-3 rounded-lg ${overdueCount > 0 ? 'bg-red-200' : 'bg-gray-100'}`}>
                <AlertCircle className={`h-6 w-6 ${overdueCount > 0 ? 'text-red-600' : 'text-gray-400'}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Kanban Board */}
      {viewMode === 'kanban' && (
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="flex gap-6 overflow-x-auto pb-4">
            <KanbanColumn
              title="📋 Pending"
              status="pending"
              items={itemsByStatus.pending}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewDetails={handleViewDetails}
            />
            <KanbanColumn
              title="🚀 In Progress"
              status="in_progress"
              items={itemsByStatus.in_progress}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewDetails={handleViewDetails}
            />
            <KanbanColumn
              title="✅ Completed"
              status="completed"
              items={itemsByStatus.completed}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onViewDetails={handleViewDetails}
            />
          </div>
        </DragDropContext>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40%]">Task</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Assignee</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {actionItems.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-12">
                        <CheckSquare className="mx-auto h-12 w-12 text-muted-foreground mb-3 opacity-50" />
                        <p className="text-sm font-medium text-gray-900">No action items yet</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Action items will appear here when extracted from calls
                        </p>
                      </TableCell>
                    </TableRow>
                  ) : (
                    actionItems.map((item) => {
                      const dueDateStatus = getDueDateStatus(item.due_date)
                      return (
                        <TableRow
                          key={item.id}
                          className={`cursor-pointer hover:bg-gray-50 ${dueDateStatus === 'overdue' ? 'bg-red-50' : ''}`}
                          onClick={() => handleViewDetails(item)}
                        >
                          <TableCell className="font-medium max-w-md">
                            <div className="space-y-1">
                              <p>{item.description}</p>
                              {dueDateStatus === 'overdue' && (
                                <Badge variant="destructive" className="text-xs">
                                  <AlertCircle className="h-3 w-3 mr-1" />
                                  Overdue
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                item.status === 'completed' ? 'success' :
                                item.status === 'in_progress' ? 'default' :
                                'secondary'
                              }
                            >
                              {item.status || 'pending'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {Array(5).fill(0).map((_, i) => (
                                <Star
                                  key={i}
                                  className={`h-3 w-3 ${
                                    i < item.priority
                                      ? 'fill-yellow-400 text-yellow-400'
                                      : 'text-gray-300'
                                  }`}
                                />
                              ))}
                            </div>
                          </TableCell>
                          <TableCell>
                            {item.assigned_to || <span className="text-muted-foreground text-xs">Unassigned</span>}
                          </TableCell>
                          <TableCell>
                            {item.due_date ? (
                              <Badge variant={getDueDateColor(dueDateStatus)} className="text-xs">
                                {format(new Date(item.due_date), 'MMM d')}
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground text-xs">No due date</span>
                            )}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-1">
                              {item.status !== 'completed' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    completeMutation.mutate(item.id)
                                  }}
                                  className="h-7"
                                >
                                  <CheckSquare className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (confirm('Are you sure you want to delete this action item?')) {
                                    handleDelete(item.id)
                                  }
                                }}
                                className="h-7 text-red-600 hover:text-red-700"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      )
                    })
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Action Item Detail Modal */}
      <ActionItemDetailModal
        item={selectedItem}
        open={showDetailModal}
        onClose={() => {
          setShowDetailModal(false)
          setSelectedItem(null)
        }}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onComplete={(id) => completeMutation.mutate(id)}
      />

      {/* Export Dialog */}
      <ExportDialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        data={actionItems}
        type="actions"
      />
    </div>
  )
}
