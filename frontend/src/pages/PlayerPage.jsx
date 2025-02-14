import { useState, useEffect } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import PlayerStats from "../components/PlayerStats";
import { PlayerPlaceholder } from "../assets/placeholder";

const PlayerPage = () => {
  const { teamId, playerId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [playerData, setPlayerData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentStats, setCurrentStats] = useState(null);
  const [careerStats, setCareerStats] = useState(null);
  const [showDetailedStats, setShowDetailedStats] = useState(false);

  useEffect(() => {
    // Scroll to top when component mounts
    window.scrollTo(0, 0);

    const fetchPlayerData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(
          `Fetching player data for player ${playerId} from team ${teamId}`
        );

        const [currentResponse, historyResponse] = await Promise.all([
          axios.get(
            `http://localhost:8000/api/teams/${teamId}/players/${playerId}`
          ),
          axios.get(
            `http://localhost:8000/api/teams/${teamId}/players/${playerId}/history`
          ),
        ]);

        console.log("Player data response:", currentResponse.data);

        if (currentResponse.data?.data) {
          setPlayerData(currentResponse.data.data);
          setCurrentStats(currentResponse.data.data.statistics?.[0]);
          setCareerStats(historyResponse.data.data.career_summary);
        } else {
          throw new Error("No player data received");
        }
      } catch (error) {
        console.error("Error fetching player data:", error);
        setError(error.response?.data?.detail || "Failed to load player data");
      } finally {
        setLoading(false);
      }
    };

    fetchPlayerData();
  }, [teamId, playerId]);

  const handleBackToTeam = () => {
    navigate(`/team/${teamId}`);
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
          <button
            onClick={handleBackToTeam}
            className="mb-4 text-blue-600 hover:text-blue-800"
          >
            ← Back to Team
          </button>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h1 className="text-xl font-bold text-red-600">Error</h1>
            <p className="text-red-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={handleBackToTeam}
          className="mb-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to Team
        </button>

        {/* Player Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center space-x-4">
            <img
              src={`https://media.api-sports.io/football/players/${playerId}.png`}
              alt={playerData.player?.name}
              className="w-32 h-32 rounded-full object-cover"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = "https://via.placeholder.com/150?text=No+Image";
              }}
            />
            <div>
              <h1 className="text-3xl font-bold">{playerData.player?.name}</h1>
              <p className="text-gray-600">
                {playerData.statistics?.[0]?.games?.position ||
                  playerData.player?.position}
              </p>
              <p className="text-gray-500">Age: {playerData.player?.age}</p>
              <p className="text-gray-500">
                Nationality: {playerData.player?.nationality}
              </p>
            </div>
          </div>
        </div>

        {/* Statistics */}
        {playerData.statistics && playerData.statistics.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">Season Statistics</h2>
              <button
                onClick={() => setShowDetailedStats(!showDetailedStats)}
                className="text-blue-600 hover:text-blue-800"
              >
                {showDetailedStats ? "− Less" : "+ More"}
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                title="Appearances"
                value={playerData.statistics[0].games?.appearences || 0}
              />
              <StatCard
                title="Goals"
                value={playerData.statistics[0].goals?.total || 0}
              />
              <StatCard
                title="Assists"
                value={playerData.statistics[0].goals?.assists || 0}
              />
              <StatCard
                title="Rating"
                value={
                  playerData.statistics[0].games?.rating?.slice(0, 4) || "-"
                }
              />
            </div>

            {showDetailedStats && (
              <div className="mt-6 space-y-4">
                <CompetitionStats
                  competitions={playerData?.statistics?.[0]?.competitions || []}
                />
                <StatBlock
                  title="Games"
                  stats={playerData.statistics[0].games}
                />
                <StatBlock
                  title="Goals & Assists"
                  stats={playerData.statistics[0].goals}
                />
                <StatBlock
                  title="Shots"
                  stats={playerData.statistics[0].shots}
                />
                <StatBlock
                  title="Passes"
                  stats={playerData.statistics[0].passes}
                />
                <StatBlock
                  title="Tackles"
                  stats={playerData.statistics[0].tackles}
                />
                <StatBlock
                  title="Duels"
                  stats={playerData.statistics[0].duels}
                />
                <StatBlock
                  title="Dribbles"
                  stats={playerData.statistics[0].dribbles}
                />
                <StatBlock
                  title="Fouls"
                  stats={playerData.statistics[0].fouls}
                />
                <StatBlock
                  title="Cards"
                  stats={playerData.statistics[0].cards}
                />
                <StatBlock
                  title="Penalties"
                  stats={playerData.statistics[0].penalty}
                />
              </div>
            )}
          </div>
        )}

        <PlayerStats currentStats={currentStats} careerStats={careerStats} />
      </div>
    </div>
  );
};

const StatCard = ({ title, value }) => (
  <div className="p-4 bg-gray-50 rounded-lg">
    <p className="text-sm text-gray-600">{title}</p>
    <p className="text-2xl font-bold">{value}</p>
  </div>
);

const StatBlock = ({ title, stats }) => (
  <div className="p-4 bg-gray-50 rounded-lg">
    <h4 className="font-semibold mb-2">{title}</h4>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key}>
          <span className="text-gray-600">{key.replace(/_/g, " ")}: </span>
          <span className="font-medium">{value || 0}</span>
        </div>
      ))}
    </div>
  </div>
);

const CompetitionStats = ({ competitions }) => {
  if (!competitions || competitions.length === 0) {
    return (
      <div className="mt-4 p-3 bg-gray-50 rounded">
        <p className="text-gray-600">No competition data available</p>
      </div>
    );
  }

  return (
    <div className="mt-4 space-y-2">
      <h4 className="font-semibold text-gray-700">
        Statistics by Competition:
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {competitions.map((comp) => (
          <div key={comp.league.id} className="bg-gray-50 p-3 rounded">
            <div className="flex items-center gap-2 mb-2">
              <img
                src={comp.league.logo}
                alt={comp.league.name}
                className="w-5 h-5"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.replaceWith(PlayerPlaceholder());
                }}
              />
              <span className="font-medium">{comp.league.name}</span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Games: </span>
                <span className="font-medium">
                  {comp.games?.appearences || 0}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Goals: </span>
                <span className="font-medium">{comp.goals?.total || 0}</span>
              </div>
              <div>
                <span className="text-gray-600">Assists: </span>
                <span className="font-medium">{comp.goals?.assists || 0}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PlayerPage;
