class InMemoryCache {
  constructor({ logger }) {
    this.entries = new Map();
    this.logger = logger;
  }

  set(key, value) {
    this.logger.info('Salvando no cache', { key });
    this.entries.set(key, value);
  }

  get(key) {
    return this.entries.get(key);
  }
}

module.exports = InMemoryCache;
