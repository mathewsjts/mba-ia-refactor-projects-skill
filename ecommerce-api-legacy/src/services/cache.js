const DEFAULT_MAX_ENTRIES = 1000;

// Cache por instância, criado no composition root; descarta a entrada mais antiga no limite.
class BoundedCache {
  constructor({ maxEntries = DEFAULT_MAX_ENTRIES, logger } = {}) {
    this.maxEntries = maxEntries;
    this.logger = logger;
    this.entries = new Map();
  }

  set(key, value) {
    this.entries.delete(key);
    this.entries.set(key, value);
    if (this.entries.size > this.maxEntries) {
      this.entries.delete(this.entries.keys().next().value);
    }
    this.logger?.debug('Salvando no cache', { key });
  }

  get(key) {
    return this.entries.get(key);
  }
}

module.exports = BoundedCache;
