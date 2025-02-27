const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  matches: `${API_BASE_URL}/api/matches`,
  teams: `${API_BASE_URL}/api/teams`,
  players: `${API_BASE_URL}/api/players`,
  leagues: `${API_BASE_URL}/api/leagues`,
  search: `${API_BASE_URL}/api/search`,
  standings: (leagueId, season) => `/api/standings/${leagueId}/${season}`,
};

export const API_CONFIG = {
  headers: {
    "Content-Type": "application/json",
  },
};

// Helper functions for common API URLs
export const getMatchUrl = (matchId) =>
  `${API_BASE_URL}/api/matches/${matchId}`;
export const getMatchCommentaryUrl = (matchId) =>
  `${API_BASE_URL}/api/matches/${matchId}/commentary`;
export const getTeamUrl = (teamId) => `${API_BASE_URL}/api/teams/${teamId}`;

export default {
  API_ENDPOINTS,
  API_CONFIG,
  getMatchUrl,
  getMatchCommentaryUrl,
  getTeamUrl,
};
