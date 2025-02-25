import { useEffect, useState } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { PlayerPlaceholder } from "../assets/placeholder";

const TeamPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [teamData, setTeamData] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [players, setPlayers] = useState([]);

  console.log("Location state:", location.state);
  console.log("Team stats:", teamStats);

  const initialTeamData = location.state?.teamData;

  useEffect(() => {
    const fetchTeamData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch team data if not provided
        if (!initialTeamData) {
          const teamResponse = await axios.get(
            `http://localhost:8000/api/teams/${id}`
          );
          setTeamData(teamResponse.data.data[0]);
        } else {
          setTeamData(initialTeamData);
        }

        // Get league ID from team data or initial data
        const leagueId =
          teamData?.team?.league?.id || initialTeamData?.league?.id;

        // Fetch team statistics with league info
        const statsResponse = await axios.get(
          `http://localhost:8000/api/teams/${id}/statistics`,
          {
            params: {
              league: leagueId,
            },
          }
        );
        console.log(
          "Raw team statistics response:",
          JSON.stringify(statsResponse.data, null, 2)
        );

        // Fetch team players
        const playersResponse = await axios.get(
          `http://localhost:8000/api/teams/${id}/players`
        );

        if (statsResponse.data?.data) {
          setTeamStats(statsResponse.data.data);
          // Store league data in sessionStorage
          if (statsResponse.data.data.league) {
            sessionStorage.setItem(
              `league_${statsResponse.data.data.league.id}`,
              JSON.stringify(statsResponse.data.data.league)
            );
          }
        }

        if (Array.isArray(playersResponse.data?.data?.players)) {
          setPlayers(playersResponse.data.data.players);
        } else {
          setPlayers([]);
        }
      } catch (error) {
        console.error("Error fetching team data:", error);
        setError("Failed to load team data");
      } finally {
        setLoading(false);
      }
    };

    fetchTeamData();
  }, [id, initialTeamData, teamData?.team?.league?.id]);

  const fetchTeamStats = async () => {
    try {
      const statsResponse = await axios.get(
        `http://localhost:8000/team/stats/${teamId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      console.log("Fetched Team Stats Response:", statsResponse.data);

      if (statsResponse.data?.data) {
        setTeamStats(statsResponse.data.data);
      } else {
        console.warn("No data returned for team statistics.");
      }
    } catch (error) {
      console.error("Error fetching team stats:", error);
    }
  };

  const handlePlayerClick = (player) => {
    navigate(`/team/${id}/player/${player.id}`, {
      state: {
        playerData: player,
        teamId: id,
      },
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-red-600">{error}</h1>
        </div>
      </div>
    );
  }

  // Extract statistics
  const matchesPlayed = teamStats?.fixtures?.played?.total || 0;
  const wins = teamStats?.fixtures?.wins?.total || 0;
  const draws = teamStats?.fixtures?.draws?.total || 0;
  const losses = teamStats?.fixtures?.loses?.total || 0;
  const winRate =
    matchesPlayed > 0 ? ((wins / matchesPlayed) * 100).toFixed(1) : 0;
  const goalsFor = teamStats?.goals?.for?.total?.total || 0;
  const goalsAgainst = teamStats?.goals?.against?.total?.total || 0;
  const cleanSheets = teamStats?.clean_sheet?.total || 0;
  const form = teamStats?.form || "";

  // Add this console.log to check the league data structure
  console.log("League data:", teamStats?.league);

  const handleBackToLeague = () => {
    if (teamStats?.league) {
      const leagueId = teamStats.league.id;
      // Store current league data in sessionStorage before navigating
      sessionStorage.setItem(
        `league_${leagueId}`,
        JSON.stringify(teamStats.league)
      );
      navigate(`/league/${leagueId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {teamStats?.league && (
          <button
            onClick={handleBackToLeague}
            className="inline-flex items-center mb-4 text-blue-600 hover:text-blue-800 transition-colors"
          >
            <span className="mr-2 text-xl">←</span>
            View {teamStats.league.name}
          </button>
        )}

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center space-x-4">
            {teamData?.team?.logo && (
              <img
                src={teamData.team.logo}
                alt={teamData.team.name}
                className="w-24 h-24 object-contain"
              />
            )}
            <div>
              <h1 className="text-3xl font-bold">{teamData?.team?.name}</h1>
              <p className="text-gray-600">{teamData?.venue?.name}</p>
              {teamStats?.league && (
                <p className="text-sm text-gray-500 mt-1">
                  {teamStats.team.name} • {teamStats.league.country}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold mb-4">Team Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Matches</p>
              <p className="text-2xl font-bold">{matchesPlayed}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Win Rate</p>
              <p className="text-2xl font-bold">{winRate}%</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Goals</p>
              <p className="text-2xl font-bold">{goalsFor}</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">Clean Sheets</p>
              <p className="text-2xl font-bold">{cleanSheets}</p>
            </div>
          </div>

          {/* Form Guide - Modified to show only last 10 matches */}
          {form && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">Last 10 Games</h3>
              <div className="flex gap-1">
                {form
                  .slice(-10)
                  .split("")
                  .map((result, index) => (
                    <div
                      key={index}
                      className={`w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold ${
                        result === "W"
                          ? "bg-green-500 text-white"
                          : result === "D"
                          ? "bg-yellow-500 text-white"
                          : "bg-red-500 text-white"
                      }`}
                    >
                      {result}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-bold mb-4">Squad</h2>

          {["Goalkeeper", "Defender", "Midfielder", "Attacker"].map(
            (position) => (
              <div key={position} className="mb-8">
                <h3 className="text-lg font-semibold mb-4 text-gray-700">
                  {position}s
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {players
                    .filter((player) => player.position === position)
                    .map((player) => (
                      <div
                        key={player.id}
                        onClick={() => handlePlayerClick(player)}
                        className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        <img
                          src={
                            player.photo ||
                            `https://media.api-sports.io/football/players/${player.id}.png`
                          }
                          alt={player.name}
                          className="w-16 h-16 rounded-full object-cover bg-gray-100"
                          onError={(e) => {
                            e.target.onerror = null;
                            const placeholder = document.createElement("div");
                            placeholder.className =
                              "w-16 h-16 rounded-full bg-gray-200 flex items-center justify-center";
                            placeholder.innerHTML = `<svg class="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                            </svg>`;
                            e.target.parentNode.replaceChild(
                              placeholder,
                              e.target
                            );
                          }}
                        />
                        <div>
                          <p className="font-semibold hover:text-blue-600">
                            {player.name}
                          </p>
                          <p className="text-sm text-gray-600">
                            {player.number && `#${player.number}`}{" "}
                            {player.position}
                          </p>
                          <p className="text-sm text-gray-500">
                            {player.age && `Age: ${player.age}`}
                          </p>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )
          )}

          {players.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              No squad information available
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TeamPage;
