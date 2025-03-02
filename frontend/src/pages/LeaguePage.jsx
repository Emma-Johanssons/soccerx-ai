import React, { useEffect, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import LeagueStandings from "../components/League/LeagueStandings";

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const LeaguePage = () => {
  console.log("LeaguePage mounting");
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [leagueData, setLeagueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLeagueData = async () => {
      try {
        setLoading(true);
        setError(null);

        // First try to get league data from location state
        if (location.state?.leagueInfo) {
          setLeagueData(location.state.leagueInfo);
          // Also store in sessionStorage for future use
          sessionStorage.setItem(
            `league_${id}`,
            JSON.stringify(location.state.leagueInfo)
          );
          setLoading(false);
          return;
        }

        // Then try sessionStorage
        const storedLeagueData = sessionStorage.getItem(`league_${id}`);
        if (storedLeagueData) {
          setLeagueData(JSON.parse(storedLeagueData));
          setLoading(false);
          return;
        }

        // If not found in either place, fetch from API
        const response = await axios.get(`${API_BASE_URL}/api/leagues/${id}`);
        if (response.data) {
          const newLeagueData = response.data;
          setLeagueData(newLeagueData);
          sessionStorage.setItem(`league_${id}`, JSON.stringify(newLeagueData));
        }
      } catch (error) {
        console.error("Error fetching league data:", error);
        setError("Failed to load league data");
      } finally {
        setLoading(false);
      }
    };

    fetchLeagueData();
  }, [id, location.state]);

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

  if (!leagueData) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-600">League not found</h1>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center space-x-4">
            {leagueData.logo && (
              <img
                src={leagueData.logo}
                alt={leagueData.name}
                className="w-24 h-24 object-contain"
              />
            )}
            <div>
              <h1 className="text-3xl font-bold">{leagueData.name}</h1>
              {leagueData.country && (
                <p className="text-gray-600">{leagueData.country}</p>
              )}
            </div>
          </div>
        </div>

        {/* Add LeagueStandings component */}
        <LeagueStandings leagueId={id} />
      </div>
    </div>
  );
};

export default LeaguePage;
