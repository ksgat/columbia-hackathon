import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { RealtimeChannel } from '@supabase/supabase-js'

type TableName = 'markets' | 'trades' | 'narrative_events' | 'resolution_votes' | 'anomaly_flags'

interface UseSupabaseRealtimeOptions {
  table: TableName
  event?: 'INSERT' | 'UPDATE' | 'DELETE' | '*'
  filter?: string
  onInsert?: (payload: any) => void
  onUpdate?: (payload: any) => void
  onDelete?: (payload: any) => void
  onChange?: (payload: any) => void
}

export function useSupabaseRealtime({
  table,
  event = '*',
  filter,
  onInsert,
  onUpdate,
  onDelete,
  onChange,
}: UseSupabaseRealtimeOptions) {
  useEffect(() => {
    let channel: RealtimeChannel

    const setupSubscription = () => {
      channel = supabase.channel(`${table}-changes`)

      if (filter) {
        channel = channel.on(
          'postgres_changes',
          { event, schema: 'public', table, filter },
          (payload) => handlePayload(payload)
        )
      } else {
        channel = channel.on(
          'postgres_changes',
          { event, schema: 'public', table },
          (payload) => handlePayload(payload)
        )
      }

      channel.subscribe()
    }

    const handlePayload = (payload: any) => {
      if (onChange) {
        onChange(payload)
      }

      switch (payload.eventType) {
        case 'INSERT':
          onInsert?.(payload.new)
          break
        case 'UPDATE':
          onUpdate?.(payload.new)
          break
        case 'DELETE':
          onDelete?.(payload.old)
          break
      }
    }

    setupSubscription()

    return () => {
      if (channel) {
        supabase.removeChannel(channel)
      }
    }
  }, [table, event, filter])
}
