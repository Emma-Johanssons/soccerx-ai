import axios from "axios";
import { getMatchCommentaryUrl } from "../config/api";

/**
 * @typedef {Object} Commentary
 * @property {number} id
 * @property {number} minute
 * @property {string} commentary
 * @property {string} event_type
 * @property {string} created_at
 */

class CommentaryService {
  constructor() {
    /** @type {Map<number, Commentary[]>} */
    this.commentaryCache = new Map();
    /** @type {Set<number>} */
    this.activeMatches = new Set();
    /** @type {number | null} */
    this.pollingInterval = null;
    /** @type {Map<number, number>} */
    this.lastFetchTime = new Map();
    /** @type {Map<number, number>} */
    this.failedAttempts = new Map();
  }

  startPolling() {
    if (!this.pollingInterval) {
      this.pollingInterval = setInterval(() => {
        this.updateAllActiveMatches();
      }, 30000); // Poll every 30 seconds
    }
  }

  /**
   * @param {number} matchId
   * @returns {Promise<void>}
   */
  async fetchCommentary(matchId) {
    try {
      const lastFetch = this.lastFetchTime.get(matchId) || 0;
      const now = Date.now();
      const failedAttempts = this.failedAttempts.get(matchId) || 0;

      // Exponential backoff for failed attempts
      const backoffTime = Math.min(30000 * Math.pow(2, failedAttempts), 300000); // Max 5 minutes

      if (now - lastFetch < backoffTime) {
        return;
      }

      const response = await axios.get(getMatchCommentaryUrl(matchId));
      if (response.data?.status === "success") {
        this.commentaryCache.set(matchId, response.data.data.commentary);
        this.lastFetchTime.set(matchId, now);
        this.failedAttempts.set(matchId, 0); // Reset failed attempts on success
      }
    } catch (error) {
      console.error(`Error fetching commentary for match ${matchId}:`, error);
      // Increment failed attempts
      const attempts = (this.failedAttempts.get(matchId) || 0) + 1;
      this.failedAttempts.set(matchId, attempts);
    }
  }

  async updateAllActiveMatches() {
    const promises = Array.from(this.activeMatches).map(async (matchId) => {
      await this.fetchCommentary(matchId);
    });
    await Promise.all(promises);
  }

  /**
   * @param {number} matchId
   */
  addMatch(matchId) {
    if (!this.activeMatches.has(matchId)) {
      this.activeMatches.add(matchId);
      this.fetchCommentary(matchId); // Initial fetch
      this.startPolling();
    }
  }

  /**
   * @param {number} matchId
   */
  removeMatch(matchId) {
    this.activeMatches.delete(matchId);
    this.commentaryCache.delete(matchId);
    this.lastFetchTime.delete(matchId);
    this.failedAttempts.delete(matchId);

    if (this.activeMatches.size === 0 && this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }
  }

  /**
   * @param {number} matchId
   * @returns {Commentary[]}
   */
  getCommentary(matchId) {
    return this.commentaryCache.get(matchId) || [];
  }
}

export const commentaryService = new CommentaryService();
