import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Phone, Search, Filter, ChevronDown, ChevronUp, X,
  Clock, Calendar, TrendingUp, AlertCircle, FileText, Download
} from 'lucide-react'
import { format } from 'date-fns'
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
} from './ui/dialog'
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
import { formatDuration, formatPhoneNumber } from '@/lib/utils'

// Debounce hook
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useMemo(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Call Detail Modal Component
function CallDetailModal({ call, open, onClose }) {
  const [fullCallData, setFullCallData] = useState(null)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)

  // Fetch full call details when modal opens
  useMemo(() => {
    if (open && call?.id) {
      setIsLoadingDetails(true)
      api.get(`/calls/${call.id}`)
        .then(response => {
          setFullCallData(response.data)
          setIsLoadingDetails(false)
        })
        .catch(error => {
          console.error('Failed to fetch call details:', error)
          setIsLoadingDetails(false)
        })
    } else {
      setFullCallData(null)
    }
  }, [open, call?.id])

  if (!call) return null

  const displayCall = fullCallData || call

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'success'
      case 'negative': return 'destructive'
      default: return 'secondary'
    }
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5 text-primary" />
            Call Details
          </DialogTitle>
          <DialogDescription>
            {format(new Date(displayCall.start_time), 'MMMM d, yyyy h:mm a')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {isLoadingDetails && (
            <div className="flex justify-center py-8">
              <div className="text-sm text-muted-foreground">Loading call details...</div>
            </div>
          )}

          {/* Call Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Caller</p>
              <p className="text-sm font-semibold">{displayCall.caller_name || 'Unknown'}</p>
              <p className="text-xs text-muted-foreground">{formatPhoneNumber(displayCall.caller_number)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Duration</p>
              <p className="text-sm font-semibold">{formatDuration(displayCall.duration_seconds)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Direction</p>
              <p className="text-sm font-semibold capitalize">{displayCall.direction || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Recording</p>
              <Badge variant={displayCall.has_recording ? 'success' : 'secondary'}>
                {displayCall.has_recording ? 'Available' : 'Not Available'}
              </Badge>
            </div>
          </div>

          {/* Sentiment & Urgency */}
          {(displayCall.summary?.sentiment || displayCall.sentiment) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-2">Sentiment</p>
                <Badge variant={getSentimentColor(displayCall.summary?.sentiment || displayCall.sentiment)}>
                  {displayCall.summary?.sentiment || displayCall.sentiment}
                </Badge>
              </div>
              {(displayCall.summary?.urgency_score || displayCall.urgency_score) && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">Urgency</p>
                  <div className="flex items-center gap-2">
                    <Badge variant={(displayCall.summary?.urgency_score || displayCall.urgency_score) >= 4 ? 'destructive' : 'secondary'}>
                      {displayCall.summary?.urgency_score || displayCall.urgency_score}/5
                    </Badge>
                    {(displayCall.summary?.urgency_score || displayCall.urgency_score) >= 4 && <AlertCircle className="h-4 w-4 text-red-500" />}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Summary */}
          {displayCall.summary?.summary && (
            <div>
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4" />
                AI Summary
              </h4>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-gray-700">{displayCall.summary.summary}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Key Topics */}
          {displayCall.summary?.key_topics && displayCall.summary.key_topics.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {displayCall.summary.key_topics.map((topic, idx) => (
                  <Badge key={idx} variant="outline">{topic}</Badge>
                ))}
              </div>
            </div>
          )}

          {/* Transcript */}
          {displayCall.summary?.transcript && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Full Transcript</h4>
              <Card>
                <CardContent className="p-4 max-h-[300px] overflow-y-auto">
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{displayCall.summary.transcript}</p>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Recording URL */}
          {displayCall.recording_url && (
            <div>
              <Button variant="outline" className="w-full" asChild>
                <a href={displayCall.recording_url} target="_blank" rel="noopener noreferrer">
                  <Phone className="mr-2 h-4 w-4" />
                  Play Recording
                </a>
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Loading Skeleton
function CallTableSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center space-x-4">
          <Skeleton className="h-12 w-full" />
        </div>
      ))}
    </div>
  )
}

export default function CallList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [showFilters, setShowFilters] = useState(false)
  const [selectedCall, setSelectedCall] = useState(null)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [sortBy, setSortBy] = useState('start_time')
  const [sortOrder, setSortOrder] = useState('desc')

  // Filters
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [directionFilter, setDirectionFilter] = useState('all')
  const [hasRecordingFilter, setHasRecordingFilter] = useState('all')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const debouncedSearch = useDebounce(searchQuery, 500)

  // Fetch calls with React Query
  const { data: callsData, isLoading, error } = useQuery({
    queryKey: ['calls', {
      search: debouncedSearch,
      sentiment: sentimentFilter,
      direction: directionFilter,
      hasRecording: hasRecordingFilter,
      page,
      pageSize,
      sortBy,
      sortOrder
    }],
    queryFn: async () => {
      const params = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        order: sortOrder
      }

      if (debouncedSearch) params.search = debouncedSearch
      if (sentimentFilter !== 'all') params.sentiment = sentimentFilter
      if (directionFilter !== 'all') params.direction = directionFilter
      if (hasRecordingFilter === 'yes') params.has_recording = true
      if (hasRecordingFilter === 'no') params.has_recording = false

      const response = await api.get('/calls', { params })
      return response.data
    },
    keepPreviousData: true,
  })

  const calls = callsData?.calls || callsData || []
  const totalCalls = callsData?.total || calls.length

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSentimentFilter('all')
    setDirectionFilter('all')
    setHasRecordingFilter('all')
    setPage(1)
  }

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return 'success'
      case 'negative': return 'destructive'
      default: return 'secondary'
    }
  }

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return <ChevronDown className="h-4 w-4 opacity-30" />
    return sortOrder === 'asc' ?
      <ChevronUp className="h-4 w-4" /> :
      <ChevronDown className="h-4 w-4" />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Call History</h2>
          <p className="mt-1 text-sm text-gray-500">
            Search, filter, and review all your calls
          </p>
        </div>
        <Button
          onClick={() => setShowExportDialog(true)}
          variant="outline"
          className="gap-2"
          disabled={!calls || calls.length === 0}
        >
          <Download className="h-4 w-4" />
          Export
        </Button>
      </div>

      {/* Search & Filter Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="space-y-4">
            {/* Search */}
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by caller name, phone number, or keywords..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="gap-2"
              >
                <Filter className="h-4 w-4" />
                Filters
                {(sentimentFilter !== 'all' || directionFilter !== 'all' || hasRecordingFilter !== 'all') && (
                  <Badge variant="destructive" className="ml-1">
                    {[sentimentFilter, directionFilter, hasRecordingFilter].filter(f => f !== 'all').length}
                  </Badge>
                )}
              </Button>
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
                <div>
                  <label className="text-sm font-medium mb-2 block">Sentiment</label>
                  <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Sentiments</SelectItem>
                      <SelectItem value="positive">Positive</SelectItem>
                      <SelectItem value="neutral">Neutral</SelectItem>
                      <SelectItem value="negative">Negative</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Direction</label>
                  <Select value={directionFilter} onValueChange={setDirectionFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Directions</SelectItem>
                      <SelectItem value="inbound">Inbound</SelectItem>
                      <SelectItem value="outbound">Outbound</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Recording</label>
                  <Select value={hasRecordingFilter} onValueChange={setHasRecordingFilter}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Calls</SelectItem>
                      <SelectItem value="yes">Has Recording</SelectItem>
                      <SelectItem value="no">No Recording</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="md:col-span-3 flex justify-end">
                  <Button variant="ghost" onClick={clearFilters} className="gap-2">
                    <X className="h-4 w-4" />
                    Clear Filters
                  </Button>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {isLoading ? 'Loading...' : `Showing ${calls.length} of ${totalCalls} calls`}
        </p>
      </div>

      {/* Calls Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6">
              <CallTableSkeleton />
            </div>
          ) : error ? (
            <div className="p-12 text-center">
              <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Error Loading Calls</h3>
              <p className="text-sm text-muted-foreground">
                {error.message || 'Failed to fetch calls. Please try again.'}
              </p>
            </div>
          ) : calls.length === 0 ? (
            <div className="p-12 text-center">
              <Phone className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Calls Found</h3>
              <p className="text-sm text-muted-foreground">
                {searchQuery || sentimentFilter !== 'all' || directionFilter !== 'all'
                  ? 'Try adjusting your search or filters'
                  : 'Calls will appear here once processed'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('start_time')}
                    >
                      <div className="flex items-center gap-2">
                        Time
                        <SortIcon column="start_time" />
                      </div>
                    </TableHead>
                    <TableHead>Caller</TableHead>
                    <TableHead>Direction</TableHead>
                    <TableHead
                      className="cursor-pointer select-none"
                      onClick={() => handleSort('duration_seconds')}
                    >
                      <div className="flex items-center gap-2">
                        Duration
                        <SortIcon column="duration_seconds" />
                      </div>
                    </TableHead>
                    <TableHead>Sentiment</TableHead>
                    <TableHead>Urgency</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {calls.map((call) => (
                    <TableRow
                      key={call.id}
                      className="cursor-pointer"
                      onClick={() => setSelectedCall(call)}
                    >
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium">
                            {format(new Date(call.start_time), 'MMM d, yyyy')}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(call.start_time), 'h:mm a')}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-sm font-medium">{call.caller_name || 'Unknown'}</span>
                          <span className="text-xs text-muted-foreground">
                            {formatPhoneNumber(call.caller_number)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {call.direction || 'N/A'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{formatDuration(call.duration_seconds)}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {call.sentiment ? (
                          <Badge variant={getSentimentColor(call.sentiment)}>
                            {call.sentiment}
                          </Badge>
                        ) : (
                          <span className="text-sm text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {call.urgency ? (
                          <div className="flex items-center gap-2">
                            <Badge variant={call.urgency >= 4 ? 'destructive' : 'secondary'}>
                              {call.urgency}/5
                            </Badge>
                            {call.urgency >= 4 && <TrendingUp className="h-4 w-4 text-red-500" />}
                          </div>
                        ) : (
                          <span className="text-sm text-muted-foreground">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedCall(call)
                          }}
                        >
                          View Details
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {!isLoading && calls.length > 0 && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page}
          </span>
          <Button
            variant="outline"
            onClick={() => setPage(p => p + 1)}
            disabled={calls.length < pageSize}
          >
            Next
          </Button>
        </div>
      )}

      {/* Call Detail Modal */}
      <CallDetailModal
        call={selectedCall}
        open={!!selectedCall}
        onClose={() => setSelectedCall(null)}
      />

      {/* Export Dialog */}
      <ExportDialog
        open={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        data={calls}
        type="calls"
      />
    </div>
  )
}
