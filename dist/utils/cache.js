"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getCachedHolderCount = getCachedHolderCount;
exports.setCachedHolderCount = setCachedHolderCount;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
const holderCountCache = new Map();
function getCachedHolderCount(address) {
    const cached = holderCountCache.get(address);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        return cached.value;
    }
    return null;
}
function setCachedHolderCount(address, count) {
    holderCountCache.set(address, {
        value: count,
        timestamp: Date.now()
    });
}
