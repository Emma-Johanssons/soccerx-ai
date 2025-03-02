import { useEffect, useState } from "react";
import { useParams, useLocation, Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { PlayerPlaceholder } from "../assets/placeholder";
import TeamStatistics from "../components/Team/TeamStatistics";

const TeamPage = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [teamData, setTeamData] = useState(null);
  const [teamStats, setTeamStats] = useState(null);
  const [players, setPlayers] = useState([]);

  // Get league info from location state
  const leagueInfo =
    location.state?.leagueInfo || teamStats?.by_league?.[0]?.league;

  console.log("Location state:", location.state);
  console.log("League info:", leagueInfo);
  console.log("Team stats:", teamStats);

  // Function to find the domestic league
  const findDomesticLeague = (teamStats) => {
    const teamCountry = teamStats?.overall?.team?.country?.toLowerCase();
    const MAJOR_LEAGUES = {
      england: "Premier League",
      spain: "La Liga",
      italy: "Serie A",
      germany: "Bundesliga",
      france: "Ligue 1",
    };

    // First try to find the league in the available leagues
    const domesticLeagues = teamStats?.by_league?.filter((stat) => {
      const leagueName = stat.league?.name?.toLowerCase() || "";
      const leagueCountry = stat.league?.country?.toLowerCase() || "";

      // Basic checks for any domestic league - removed leagueType check
      const isDomestic =
        leagueCountry === teamCountry &&
        !leagueName.includes("cup") &&
        !leagueName.includes("champions") &&
        !leagueName.includes("europa") &&
        !leagueName.includes("friendly") &&
        !leagueName.includes("super");

      console.log(`Checking league: ${stat.league?.name}`, {
        leagueName,
        leagueCountry,
        teamCountry,
        isDomestic,
        fullLeague: stat.league, // Log full league object for debugging
      });

      return isDomestic;
    });

    if (domesticLeagues.length === 0) {
      console.log(
        "Available leagues:",
        teamStats?.by_league?.map((stat) => ({
          name: stat.league?.name,
          country: stat.league?.country,
        }))
      );
      console.log("No domestic leagues found for country:", teamCountry);
      return null;
    }

    // If it's a major league country, try to find the specific league first
    if (MAJOR_LEAGUES[teamCountry]) {
      const expectedLeagueName = MAJOR_LEAGUES[teamCountry].toLowerCase();
      const majorLeague = domesticLeagues.find((stat) =>
        stat.league?.name?.toLowerCase().includes(expectedLeagueName)
      );
      if (majorLeague) {
        console.log("Found major league:", majorLeague.league);
        return majorLeague.league;
      }
    }

    // Sort leagues by priority
    const sortedLeagues = domesticLeagues.sort((a, b) => {
      const nameA = a.league?.name?.toLowerCase() || "";
      const nameB = b.league?.name?.toLowerCase() || "";

      // Check for division numbers
      const divA = nameA.match(/\d+/) ? parseInt(nameA.match(/\d+/)[0]) : 0;
      const divB = nameB.match(/\d+/) ? parseInt(nameB.match(/\d+/)[0]) : 0;

      if (divA === divB) {
        return nameA.length - nameB.length;
      }
      return divA - divB;
    });

    console.log(
      "Sorted leagues:",
      sortedLeagues.map((l) => l.league?.name)
    );
    return sortedLeagues[0]?.league;
  };

  const handleBackToLeague = () => {
    const domesticLeague = findDomesticLeague(teamStats);
    console.log("Found domestic league:", domesticLeague);

    if (domesticLeague?.id) {
      try {
        const leagueData = {
          id: domesticLeague.id,
          name: domesticLeague.name,
          country: domesticLeague.country,
          logo: domesticLeague.logo,
          type: domesticLeague.type,
          season: domesticLeague.season,
        };

        console.log("Attempting navigation to league:", leagueData);

        // Store in session storage before navigation
        sessionStorage.setItem(
          `league_${domesticLeague.id}`,
          JSON.stringify(leagueData)
        );

        // Force navigation to league page
        window.location.href = `/league/${domesticLeague.id}`;
      } catch (error) {
        console.error("Navigation error:", error);
      }
    } else {
      console.error("No domestic league found for this team");
    }
  };

  useEffect(() => {
    const fetchTeamData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch team data if not provided
        if (!location.state?.teamData) {
          const teamResponse = await axios.get(
            `${process.env.REACT_APP_API_BASE_URL}/api/teams/${id}`
          );
          setTeamData(teamResponse.data.data[0]);
        } else {
          setTeamData(location.state.teamData);
        }

        // Fetch team statistics
        const statsResponse = await axios.get(
          `${process.env.REACT_APP_API_BASE_URL}/api/teams/${id}/statistics`
        );
        console.log("Raw team statistics response:", statsResponse.data);
        console.log("Team stats:", statsResponse.data?.data?.overall?.team);
        console.log("League data:", statsResponse.data?.data?.overall?.league);
        console.log(
          "Coach data:",
          statsResponse.data?.data?.overall?.team?.coach
        );

        if (statsResponse.data?.data) {
          setTeamStats(statsResponse.data.data);
        }

        // Fetch team players
        const playersResponse = await axios.get(
          `${process.env.REACT_APP_API_BASE_URL}/api/teams/${id}/players`
        );

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
  }, [id]);

  // Add this debug log to see what data we have
  useEffect(() => {
    console.log("Current teamStats:", teamStats);
    console.log("Location state:", location.state);
  }, [teamStats, location.state]);

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
  const matchesPlayed = teamStats?.overall?.fixtures?.played?.total || 0;
  const wins = teamStats?.overall?.fixtures?.wins?.total || 0;
  const draws = teamStats?.overall?.fixtures?.draws?.total || 0;
  const losses = teamStats?.overall?.fixtures?.loses?.total || 0;
  const winRate =
    matchesPlayed > 0 ? ((wins / matchesPlayed) * 100).toFixed(1) : 0;
  const goalsFor = teamStats?.overall?.goals?.for?.total?.total || 0;
  const goalsAgainst = teamStats?.overall?.goals?.against?.total?.total || 0;
  const cleanSheets = teamStats?.overall?.clean_sheet?.total || 0;
  const form = teamStats?.form || "";

  // Add this console.log to check the league data structure
  console.log("League data:", teamStats?.league);

  const leagueName =
    teamData?.team?.league?.name || location.state?.leagueName || "League";

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {teamStats &&
          (() => {
            const domesticLeague = findDomesticLeague(teamStats);
            console.log("Domestic league for button:", domesticLeague);

            return domesticLeague?.id ? (
              <button
                onClick={() => handleBackToLeague()}
                className="mb-4 flex items-center text-blue-600 hover:text-blue-800 cursor-pointer"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
                Back to {domesticLeague.name}
              </button>
            ) : null;
          })()}

        {/* Team Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center gap-6">
            {teamStats?.overall?.team?.logo && (
              <img
                src={teamStats.overall.team.logo}
                alt={teamStats.overall.team.name}
                className="w-24 h-24 object-contain"
              />
            )}
            <div>
              <h1 className="text-3xl font-bold">
                {teamStats?.overall?.team?.name}
              </h1>
            </div>
          </div>
        </div>

        {/* Team Statistics Component */}
        <TeamStatistics statistics={teamStats} />

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
