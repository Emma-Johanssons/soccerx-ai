import { useState, useEffect } from "react";
import axios from "axios";

const MAJOR_LEAGUES = {
  "Premier League": true, // ID: 39
  "DFB Pokal": true, // ID: 81
  "Copa del Rey": true, // ID: 143
  Bundesliga: true, // ID: 78
  "La Liga": true, // ID: 140
  "Serie A": true, // ID: 135
  "Ligue 1": true, // ID: 61
  "Champions League": true, // ID: 2
  "Europa League": true, // ID: 3
  "Coppa Italia": true, // ID: 137
};

const MatchList = ({ completed = false }) => {
  const [matches, setMatches] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAllLeagues, setShowAllLeagues] = useState(false);
  const [expandedMatch, setExpandedMatch] = useState(null);

  useEffect(() => {
    const fetchMatches = async () => {
      try {
        setLoading(true);
        console.log(
          `Fetching matches for ${completed ? "completed" : "today"} tab`
        );
        const response = await axios.get(
          `http://localhost:8000/api/matches?completed=${completed}`
        );
        const matchesData = response.data.data || [];

        // Group matches by league
        const groupedMatches = matchesData.reduce((acc, match) => {
          if (!match.league || !match.league.name) return acc;

          const leagueName = match.league.name;
          const matchStatus = match.fixture?.status?.short || "";

          // Special check for Premier League to ensure it's the correct one (ID: 39)
          if (leagueName === "Premier League" && match.league.id !== 39) {
            return acc;
          }

          if (!acc[leagueName]) {
            acc[leagueName] = [];
          }

          acc[leagueName].push({
            id: match.fixture?.id || Math.random(),
            time: match.fixture?.date
              ? new Date(match.fixture.date).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              : "--:--",
            timestamp: match.fixture?.date
              ? new Date(match.fixture.date).getTime()
              : 0,
            status: matchStatus,
            isLive: ["1H", "2H", "HT", "ET", "P", "LIVE"].includes(matchStatus),
            elapsedTime: match.fixture?.elapsed,
            homeTeam: match.teams?.home?.name || "TBD",
            awayTeam: match.teams?.away?.name || "TBD",
            homeScore: match.goals?.home,
            awayScore: match.goals?.away,
            homeLogo: match.teams?.home?.logo || "",
            awayLogo: match.teams?.away?.logo || "",
            competition: match.league.name,
          });

          return acc;
        }, {});

        // Sort matches within each league by timestamp
        Object.keys(groupedMatches).forEach((leagueName) => {
          groupedMatches[leagueName].sort((a, b) => a.timestamp - b.timestamp);
        });

        setMatches(groupedMatches);
      } catch (error) {
        console.error("Error fetching matches:", error);
        setError("Failed to load matches");
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [completed]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-10">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-center py-10 text-red-500">{error}</div>;
  }

  const filteredLeagues = Object.entries(matches)
    // First filter the leagues
    .filter(([leagueName]) => showAllLeagues || MAJOR_LEAGUES[leagueName])
    // Then sort the leagues by match time instead of alphabetically
    .sort(([aLeagueName, aMatches], [bLeagueName, bMatches]) => {
      // Get the earliest match time from each league
      const aTime = aMatches[0]?.timestamp || 0;
      const bTime = bMatches[0]?.timestamp || 0;
      return aTime - bTime; // Sort leagues by their earliest match time
    });

  return (
    <div className="space-y-4">
      {/* League Filter */}
      <div className="flex justify-end px-4">
        <button
          onClick={() => setShowAllLeagues(!showAllLeagues)}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          {showAllLeagues ? "Show Major Leagues" : "View All Leagues"}
        </button>
      </div>

      {/* Matches */}
      {filteredLeagues.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          No matches {completed ? "completed" : "scheduled"} today
        </div>
      ) : (
        filteredLeagues.map(([leagueName, leagueMatches]) => (
          <div
            key={leagueName}
            className="bg-white rounded-lg shadow overflow-hidden"
          >
            <div className="bg-[#1a2b4b] text-white px-4 py-2">
              <h2 className="text-lg font-semibold">{leagueName}</h2>
            </div>

            <div className="divide-y divide-gray-200">
              {Array.isArray(leagueMatches) &&
                leagueMatches.map((match) => (
                  <div key={match.id}>
                    <div className="p-4 hover:bg-gray-50 transition-all cursor-pointer">
                      <div className="flex items-center justify-between">
                        <div className="w-20 text-center relative">
                          <div className="text-sm font-medium text-gray-900">
                            {match.time}
                          </div>
                          {match.isLive ? (
                            <div className="absolute -top-2 left-0 right-0">
                              <div className="inline-block px-2 py-1 bg-red-500 text-white text-xs font-semibold rounded-full shadow-sm">
                                LIVE{" "}
                                {match.elapsedTime && `${match.elapsedTime}'`}
                              </div>
                            </div>
                          ) : (
                            <div className="text-xs text-gray-500">
                              {match.status}
                            </div>
                          )}
                        </div>

                        <div className="flex-1 px-4">
                          <div className="flex justify-between items-center mb-3">
                            <div className="flex items-center space-x-3">
                              {match.homeLogo && (
                                <img
                                  src={match.homeLogo}
                                  alt={`${match.homeTeam} logo`}
                                  className="w-6 h-6 object-contain"
                                />
                              )}
                              <span className="font-medium text-gray-900">
                                {match.homeTeam}
                              </span>
                            </div>
                            <span className="font-semibold text-gray-900">
                              {match.homeScore ?? "-"}
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <div className="flex items-center space-x-3">
                              {match.awayLogo && (
                                <img
                                  src={match.awayLogo}
                                  alt={`${match.awayTeam} logo`}
                                  className="w-6 h-6 object-contain"
                                />
                              )}
                              <span className="font-medium text-gray-900">
                                {match.awayTeam}
                              </span>
                            </div>
                            <span className="font-semibold text-gray-900">
                              {match.awayScore ?? "-"}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
};

export default MatchList;
