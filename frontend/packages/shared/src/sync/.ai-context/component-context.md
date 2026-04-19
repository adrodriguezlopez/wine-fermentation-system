# Component Context: Sync Queue (`packages/shared/src/sync/`)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions

## Component responsibility

**Offline write queue** for the mobile app. When the device has no network, write operations (sample recording, action recording, step completion) are enqueued to AsyncStorage instead of being sent immediately. When network connectivity is restored, the queue flushes in order, replaying the mutations against the live API.

This component is **mobile-only in practice** but lives in `packages/shared` so it can be tested independently and potentially used in a future desktop offline scenario.

## Architecture pattern

`SyncQueue` class + `NetInfo` (Expo network state) listener for flush trigger.

## Files

### `SyncQueue.ts`

```typescript
interface QueuedMutation {
  id: string           // uuid — idempotency key
  endpoint: string     // e.g. '/api/v1/fermentations/xxx/samples'
  method: 'POST' | 'PATCH'
  body: unknown
  timestamp: number    // ms since epoch — for ordering
}

class SyncQueue {
  enqueue(mutation: Omit<QueuedMutation, 'id' | 'timestamp'>): Promise<void>
  flush(apiClient: ApiClient): Promise<{ succeeded: number; failed: number }>
  getQueue(): Promise<QueuedMutation[]>
  clearQueue(): Promise<void>
}
```

**Persistence**: Queue stored in `@react-native-async-storage/async-storage` under key `wfs_sync_queue`.

**Flush trigger**: Called by the mobile app's root layout on:
1. App enters foreground (`AppState` change)
2. Network connectivity restored (`NetInfo` event)

**Conflict strategy**: Last-write-wins. If two offline sample recordings target the same fermentation, both are sent in timestamp order. The backend accepts both as valid measurements.

**Operations that are queued**:
- `POST /fermentations/{id}/samples` — sample recording
- `POST /fermentations/{id}/actions` — corrective action
- `PATCH /actions/{id}/outcome` — action outcome update
- `POST /steps/{id}/complete` — protocol step completion

**Operations that are NOT queued** (require online):
- Auth (login, refresh)
- `POST /alerts/{id}/acknowledge` — real-time intent
- `POST /alerts/{id}/dismiss` — real-time intent
- `POST /fermentations/{id}/execute` — protocol execution start

## Implementation status

**Status**: 🔲 NOT STARTED — Phase 4 / Offline and Sync Layer
