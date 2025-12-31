import { useState } from 'react'
import { Download, FileText, Table as TableIcon } from 'lucide-react'
import { format } from 'date-fns'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import { Badge } from './ui/badge'
import toast from 'react-hot-toast'

// CSV Generation Helper
function convertToCSV(data, headers) {
  if (!data || data.length === 0) return ''

  const csvHeaders = headers.join(',')
  const csvRows = data.map(row => {
    return headers.map(header => {
      const value = row[header] || ''
      // Escape quotes and wrap in quotes if contains comma
      const escaped = String(value).replace(/"/g, '""')
      return escaped.includes(',') ? `"${escaped}"` : escaped
    }).join(',')
  })

  return [csvHeaders, ...csvRows].join('\n')
}

function downloadCSV(csv, filename) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}

export default function ExportDialog({ open, onClose, data, type = 'calls' }) {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [includeFilters, setIncludeFilters] = useState({
    summary: true,
    transcript: false,
    sentiment: true,
    actionItems: true,
  })

  const handleExport = () => {
    if (!data || data.length === 0) {
      toast.error('No data to export')
      return
    }

    let filteredData = data

    // Apply date filters
    if (dateFrom) {
      filteredData = filteredData.filter(item => {
        const itemDate = new Date(item.start_time || item.created_at)
        return itemDate >= new Date(dateFrom)
      })
    }

    if (dateTo) {
      filteredData = filteredData.filter(item => {
        const itemDate = new Date(item.start_time || item.created_at)
        return itemDate <= new Date(dateTo)
      })
    }

    if (filteredData.length === 0) {
      toast.error('No data matches the selected date range')
      return
    }

    // Prepare data based on type
    let csv = ''
    let filename = ''

    if (type === 'calls') {
      const processedData = filteredData.map(call => ({
        'Call ID': call.id,
        'Date': format(new Date(call.start_time), 'yyyy-MM-dd HH:mm:ss'),
        'Caller': call.caller || 'Unknown',
        'Phone': call.phone_number,
        'Direction': call.direction || 'N/A',
        'Duration (seconds)': call.duration_seconds,
        'Status': call.status,
        ...(includeFilters.sentiment && { 'Sentiment': call.sentiment || 'N/A' }),
        ...(includeFilters.sentiment && { 'Urgency': call.urgency || 'N/A' }),
        ...(includeFilters.summary && { 'Summary': call.summary || '' }),
        ...(includeFilters.transcript && { 'Transcript': call.transcript || '' }),
      }))

      const headers = Object.keys(processedData[0])
      csv = convertToCSV(processedData, headers)
      filename = `calls-export-${format(new Date(), 'yyyy-MM-dd')}.csv`
    } else if (type === 'actions') {
      const processedData = filteredData.map(item => ({
        'Action ID': item.id,
        'Description': item.description,
        'Status': item.status || 'pending',
        'Priority': item.priority || 'N/A',
        'Assigned To': item.assigned_to || '',
        'Due Date': item.due_date ? format(new Date(item.due_date), 'yyyy-MM-dd') : '',
        'Call ID': item.call_id || '',
        'Created': format(new Date(item.created_at), 'yyyy-MM-dd HH:mm:ss'),
      }))

      const headers = Object.keys(processedData[0])
      csv = convertToCSV(processedData, headers)
      filename = `action-items-export-${format(new Date(), 'yyyy-MM-dd')}.csv`
    }

    downloadCSV(csv, filename)
    toast.success(`Exported ${filteredData.length} ${type}!`)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export {type === 'calls' ? 'Calls' : 'Action Items'}
          </DialogTitle>
          <DialogDescription>
            Download your data as a CSV file
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Date Range */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Date Range (Optional)</h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">From</label>
                <Input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">To</label>
                <Input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Include Options (for calls) */}
          {type === 'calls' && (
            <div className="space-y-3">
              <h4 className="text-sm font-semibold">Include in Export</h4>
              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeFilters.summary}
                    onChange={(e) => setIncludeFilters({ ...includeFilters, summary: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">AI Summary</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeFilters.sentiment}
                    onChange={(e) => setIncludeFilters({ ...includeFilters, sentiment: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Sentiment & Urgency</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeFilters.transcript}
                    onChange={(e) => setIncludeFilters({ ...includeFilters, transcript: e.target.checked })}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm">Full Transcript</span>
                  <Badge variant="secondary" className="text-xs">Large file</Badge>
                </label>
              </div>
            </div>
          )}

          {/* Preview */}
          <div className="bg-muted p-3 rounded-lg">
            <p className="text-xs text-muted-foreground">
              {data?.length || 0} total {type} available
              {(dateFrom || dateTo) && ' (filters will be applied)'}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleExport} className="gap-2">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
