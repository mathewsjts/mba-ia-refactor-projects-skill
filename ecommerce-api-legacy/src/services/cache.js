// Cache em memória encapsulado e injetado (T11), substituindo o `globalCache`
// global mutável do utils.js original (F-07).
class InMemoryCache {
    constructor() {
        this.entries = new Map();
    }

    set(key, value) {
        this.entries.set(key, value);
    }

    get(key) {
        return this.entries.get(key);
    }
}

module.exports = InMemoryCache;
