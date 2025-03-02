import { useEffect, useState } from "react";
import { useSearchParams, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const LEAGUE_IDS = {
  "Premier League": "39",
  "La Liga": "140",
  "Serie A": "135",
  Bundesliga: "78",
  "Ligue 1": "61",
};

const SearchResults = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedLeagueId, setSelectedLeagueId] = useState(null);
  const query = searchParams.get("q");
  const searchResults = location.state?.searchResults || [];

  console.log("SearchResults component rendered");

  useEffect(() => {
    console.log("SearchResults mounted");
    console.log("Current location:", location);
    console.log("Search query:", query);

    const fetchResults = async () => {
      try {
        setLoading(true);
        setError(null);

        // Check if the search query matches any league name
        const leagueEntry = Object.entries(LEAGUE_IDS).find(([leagueName]) =>
          leagueName.toLowerCase().includes(query.toLowerCase())
        );

        if (leagueEntry) {
          const [leagueName, leagueId] = leagueEntry;
          console.log(`Found league: ${leagueName} with ID: ${leagueId}`);
          setSelectedLeagueId(leagueId);

          // Fetch league details
          const response = await axios.get(
            `${process.env.REACT_APP_API_BASE_URL}/api/leagues/${leagueId}`
          );
          const leagueData = response.data;

          // Navigate to the league page with the data
          navigate(`/league/${leagueId}`, {
            state: { leagueData: leagueData.data },
          });
          return;
        }

        // If no league found, fetch general search results
        const response = await axios.get(
          `${
            process.env.REACT_APP_API_BASE_URL
          }/api/search?q=${encodeURIComponent(query)}`
        );
        setResults(response.data.data || []);
      } catch (error) {
        console.error("Error details:", error.response || error);
        setError("Failed to fetch search results. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (query) {
      fetchResults();
    }
  }, [query, navigate]);

  useEffect(() => {
    console.log("Search Results Component:", {
      query,
      results: searchResults,
      locationState: location.state,
    });
  }, [query, searchResults, location.state]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-red-500">{error}</div>
        </div>
      </div>
    );
  }

  if (searchResults.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h2 className="text-2xl font-bold mb-4">
            No leagues found for "{query}"
          </h2>
          <p>Try searching for a different league or country name.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-2xl font-bold mb-4">
          Search results for "{query}" ({searchResults.length} results)
        </h2>

        {searchResults.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600">No leagues found for "{query}"</p>
            <p className="text-sm text-gray-500 mt-2">
              Try searching for a different league or country name.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((league) => (
              <div
                key={league.league.id}
                className="bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => {
                  console.log("Navigating to league:", league.league.id);
                  navigate(`/league/${league.league.id}`, {
                    state: { leagueData: league },
                  });
                }}
              >
                <div className="flex items-center space-x-4">
                  {league.league.logo && (
                    <img
                      src={league.league.logo}
                      alt={league.league.name}
                      className="w-12 h-12 object-contain"
                    />
                  )}
                  <div>
                    <h3 className="font-semibold">{league.league.name}</h3>
                    <p className="text-sm text-gray-600">
                      {league.country?.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      Type: {league.league.type}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchResults;
