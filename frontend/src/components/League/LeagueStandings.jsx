import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const LeagueStandings = ({ leagueId }) => {
  const navigate = useNavigate();
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [season, setSeason] = useState(null);
  const [leagueData, setLeagueData] = useState(null);

  useEffect(() => {
    const fetchCurrentSeason = async () => {
      try {
        // First, fetch league info to get the current season
        const leagueResponse = await axios.get(
          `${process.env.REACT_APP_API_BASE_URL}/api/leagues/${leagueId}`
        );

        if (leagueResponse.data?.data?.seasons?.[0]?.year) {
          return leagueResponse.data.data.seasons[0].year;
        }

        // Fallback to current year if API doesn't provide season
        return new Date().getFullYear();
      } catch (error) {
        console.error("Error fetching current season:", error);
        // Fallback to current year if there's an error
        return new Date().getFullYear();
      }
    };

    const fetchStandings = async () => {
      try {
        setLoading(true);
        // Get the current season first
        const currentSeason = await fetchCurrentSeason();
        setSeason(currentSeason);

        console.log(`Fetching standings for season ${currentSeason}`); // Debug log

        const response = await axios.get(
          `${process.env.REACT_APP_API_BASE_URL}/api/standings/${leagueId}/${currentSeason}`
        );

        console.log("Standings response:", response.data); // Debug log

        if (response.data?.data) {
          setStandings(response.data.data);
          setLeagueData(response.data.data[0].league);
        } else {
          setError("No standings data available");
        }
      } catch (error) {
        console.error("Error fetching standings:", error);
        setError("Failed to load standings");
      } finally {
        setLoading(false);
      }
    };

    if (leagueId) {
      fetchStandings();
    }
  }, [leagueId]);

  const handleTeamClick = (team) => {
    navigate(`/team/${team.team.id}`, {
      state: {
        teamData: team,
        leagueInfo: {
          id: leagueId,
          name: leagueData?.name || "League",
          logo: leagueData?.logo,
          country: leagueData?.country,
        },
      },
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-10">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4">
        <p className="text-red-500 text-center">{error}</p>
      </div>
    );
  }

  if (!standings || standings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-4">
        <p className="text-gray-500 text-center">No standings available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <h2 className="text-lg font-bold p-4 border-b flex justify-between items-center">
        <span>League Standings</span>
        {season && (
          <span className="text-sm text-gray-500">
            Season {season}/{season + 1}
          </span>
        )}
      </h2>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pos
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Team
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                P
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                W
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                D
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                L
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                GD
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pts
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {standings.map((team) => (
              <tr
                key={team.team.id}
                onClick={() => handleTeamClick(team)}
                className="hover:bg-gray-50 cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap">{team.rank}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <img
                      src={team.team.logo}
                      alt={team.team.name}
                      className="w-6 h-6 mr-2"
                    />
                    <span>{team.team.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {team.all.played}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">{team.all.win}</td>
                <td className="px-6 py-4 whitespace-nowrap">{team.all.draw}</td>
                <td className="px-6 py-4 whitespace-nowrap">{team.all.lose}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {team.goalsDiff}
                </td>
                <td className="px-6 py-4 whitespace-nowrap font-bold">
                  {team.points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LeagueStandings;
