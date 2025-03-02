import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

// Define major leagues with their IDs and variations of names
const MAJOR_LEAGUES = {
  "LA LIGA": { id: 140, variations: ["LA LIGA", "LALIGA", "SPANISH LEAGUE"] },
  "PREMIER LEAGUE": {
    id: 39,
    variations: ["PREMIER LEAGUE", "EPL", "ENGLISH PREMIER LEAGUE"],
  },
  "SERIE A": { id: 135, variations: ["SERIE A", "ITALIAN SERIE A"] },
  BUNDESLIGA: { id: 78, variations: ["BUNDESLIGA", "GERMAN BUNDESLIGA"] },
  "LIGUE 1": { id: 61, variations: ["LIGUE 1", "FRENCH LIGUE 1"] },
};

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const SearchBar = () => {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const navigate = useNavigate();
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = async (e) => {
    const searchQuery = e.target.value;
    setQuery(searchQuery);

    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(
        `${API_BASE_URL}/api/search?q=${encodeURIComponent(searchQuery)}`
      );
      setSearchResults(response.data.results || []);
      setShowDropdown(true);
    } catch (error) {
      console.error("Search error:", error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleResultClick = (result) => {
    console.log("Result clicked:", result);
    setShowDropdown(false);
    setQuery("");

    switch (result.type) {
      case "league":
        navigate(`/league/${result.id}`, {
          state: {
            leagueData: {
              league: {
                name: result.name,
                logo: result.logo,
                id: result.id,
              },
              country: {
                name: result.country,
              },
            },
          },
        });
        break;
      case "team":
        navigate(`/team/${result.id}`, { state: { teamData: result } });
        break;
      case "player":
        navigate(`/player/${result.id}`, { state: { playerData: result } });
        break;
      default:
        console.error("Unknown result type:", result.type);
    }
  };

  return (
    <div className="relative w-full max-w-xl mx-auto" ref={dropdownRef}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleSearch}
          placeholder="Search for leagues, teams, or players..."
          className="w-full p-2 pl-10 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500"
        />
        {loading && (
          <div className="absolute right-3 top-2.5">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>

      {showDropdown && searchResults.length > 0 && (
        <div className="absolute w-full mt-1 bg-white rounded-lg shadow-lg border border-gray-200 max-h-96 overflow-y-auto z-50">
          {searchResults.map((result, index) => (
            <div
              key={`${result.type}-${result.id}-${index}`}
              onClick={() => handleResultClick(result)}
              className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
            >
              <div className="flex items-center space-x-3">
                {result.logo && (
                  <img
                    src={result.logo}
                    alt={result.name}
                    className="w-8 h-8 object-contain"
                  />
                )}
                <div>
                  <div className="font-medium">{result.name}</div>
                  <div className="text-sm text-gray-500">
                    {result.type.charAt(0).toUpperCase() + result.type.slice(1)}
                    {result.country && ` • ${result.country}`}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
