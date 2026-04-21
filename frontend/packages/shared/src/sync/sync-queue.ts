// Placeholder for offline sync (Iteration 3+)
export class SyncQueue {
  private queue: Array<() => Promise<void>> = []

  enqueue(task: () => Promise<void>): void {
    this.queue.push(task)
  }

  async flush(): Promise<void> {
    while (this.queue.length > 0) {
      const task = this.queue.shift()!
      await task()
    }
  }

  get size(): number {
    return this.queue.length
  }
}
