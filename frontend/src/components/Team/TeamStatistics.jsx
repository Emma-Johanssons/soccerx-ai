import React, { useState } from "react";

const TeamStatistics = ({ statistics }) => {
  const [showAllLeagues, setShowAllLeagues] = useState(false);

  // Get current season
  const currentSeason = new Date().getFullYear();
  const seasonDisplay = `${currentSeason - 1}/${currentSeason}`;

  console.log("Received statistics:", statistics);

  // Ensure we have default values and properly structure the data
  const overall = {
    ...statistics?.overall,
    fixtures: {
      played: { total: statistics?.overall?.fixtures?.played?.total || 0 },
      wins: { total: statistics?.overall?.fixtures?.wins?.total || 0 },
      draws: { total: statistics?.overall?.fixtures?.draws?.total || 0 },
      loses: { total: statistics?.overall?.fixtures?.loses?.total || 0 },
    },
    goals: {
      for: {
        total: { total: statistics?.overall?.goals?.for?.total?.total || 0 },
      },
      against: {
        total: {
          total: statistics?.overall?.goals?.against?.total?.total || 0,
        },
      },
    },
    clean_sheet: { total: statistics?.overall?.clean_sheet?.total || 0 },
    team: statistics?.overall?.team || {},
  };

  const leagueStats = statistics?.by_league || [];
  const form = statistics?.form || [];

  // Find the domestic league (prioritizing main domestic leagues)
  const domesticLeague = leagueStats.find(
    (stat) =>
      stat.league?.type?.toLowerCase() === "league" &&
      !stat.league?.name?.toLowerCase().includes("friendly") &&
      !stat.league?.name?.toLowerCase().includes("cup") &&
      !stat.league?.name?.toLowerCase().includes("champions") &&
      !stat.league?.name?.toLowerCase().includes("europa")
  );

  // Update overall stats with domestic league info if found
  if (domesticLeague) {
    overall.league = domesticLeague.league;
  }

  console.log("Processed overall stats:", overall);

  const FormIndicator = ({ result }) => {
    const getColor = (result) => {
      switch (result.toUpperCase()) {
        case "W":
          return "bg-green-500";
        case "D":
          return "bg-yellow-500";
        case "L":
          return "bg-red-500";
        default:
          return "bg-gray-300";
      }
    };

    return (
      <div
        className={`w-8 h-8 ${getColor(
          result
        )} rounded-full flex items-center justify-center text-white font-bold`}
      >
        {result.toUpperCase()}
      </div>
    );
  };

  const TeamInfoBlock = ({ team }) => (
    <div className="mb-6 p-4 border rounded bg-gray-50">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Club & Venue Information */}
        <div>
          <h3 className="font-semibold mb-3">Club Information</h3>
          <div className="space-y-2">
            <p>
              <span className="text-gray-600">Country:</span> {team.country}
            </p>
            {team.founded && (
              <p>
                <span className="text-gray-600">Founded:</span> {team.founded}
              </p>
            )}
            {team.venue?.name && (
              <p>
                <span className="text-gray-600">Home Arena:</span>{" "}
                {team.venue.name}
              </p>
            )}
            {team.venue?.capacity && (
              <p>
                <span className="text-gray-600">Capacity:</span>{" "}
                {team.venue.capacity.toLocaleString()} seats
              </p>
            )}
          </div>
        </div>

        {/* Coach Information */}
        {team.coach && (
          <div>
            <h3 className="font-semibold mb-3">Manager</h3>
            <div className="flex items-start space-x-4">
              {team.coach.photo && (
                <img
                  src={team.coach.photo}
                  alt={team.coach.name}
                  className="w-20 h-20 object-cover rounded"
                />
              )}
              <div className="space-y-2">
                <p>
                  <span className="text-gray-600">Name:</span> {team.coach.name}
                </p>
                {team.coach.age && (
                  <p>
                    <span className="text-gray-600">Age:</span> {team.coach.age}
                  </p>
                )}
                {team.coach.nationality && (
                  <p>
                    <span className="text-gray-600">Nationality:</span>{" "}
                    {team.coach.nationality}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const StatBlock = ({ stats, title, showForm = false }) => (
    <div className="p-4 border rounded">
      <div className="flex items-center gap-2 mb-3">
        {stats.league?.logo && (
          <img
            src={stats.league.logo}
            alt={stats.league.name}
            className="w-6 h-6"
          />
        )}
        <h3 className="font-semibold">{title}</h3>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <p>Played: {stats.fixtures?.played?.total || 0}</p>
          <p>Wins: {stats.fixtures?.wins?.total || 0}</p>
          <p>Draws: {stats.fixtures?.draws?.total || 0}</p>
          <p>Losses: {stats.fixtures?.loses?.total || 0}</p>
        </div>
        <div>
          <p>Goals For: {stats.goals?.for?.total?.total || 0}</p>
          <p>Goals Against: {stats.goals?.against?.total?.total || 0}</p>
          <p>Clean Sheets: {stats.clean_sheet?.total || 0}</p>
        </div>
      </div>

      {/* Form display only for overall stats */}
      {showForm && form && form.length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">Last 5 matches:</p>
          <div className="flex gap-2">
            {form.slice(0, 5).map((result, index) => (
              <FormIndicator key={index} result={result} />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white shadow rounded-lg p-6">
      {/* Team Info Block */}
      {overall.team && <TeamInfoBlock team={overall.team} />}

      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Team Statistics</h2>
        <button
          onClick={() => setShowAllLeagues(!showAllLeagues)}
          className="text-blue-600 hover:text-blue-800"
        >
          {showAllLeagues ? "Show Less" : "Show All Competitions"}
        </button>
      </div>

      {/* Overall Statistics with Form */}
      <div className="p-4 border rounded">
        <div className="flex items-center gap-2 mb-3">
          <img
            src={overall.team.logo}
            alt={overall.team.name}
            className="w-6 h-6"
          />
          <h3 className="font-semibold">Overall Statistics {seasonDisplay}</h3>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div>
            <p>Played: {overall.fixtures?.played?.total || 0}</p>
            <p>Wins: {overall.fixtures?.wins?.total || 0}</p>
            <p>Draws: {overall.fixtures?.draws?.total || 0}</p>
            <p>Losses: {overall.fixtures?.loses?.total || 0}</p>
          </div>
          <div>
            <p>Goals For: {overall.goals?.for?.total?.total || 0}</p>
            <p>Goals Against: {overall.goals?.against?.total?.total || 0}</p>
            <p>Clean Sheets: {overall.clean_sheet?.total || 0}</p>
          </div>
        </div>

        {form && form.length > 0 && (
          <div className="mt-4">
            <p className="text-sm text-gray-600 mb-2">Last 5 matches:</p>
            <div className="flex gap-2">
              {form.slice(0, 5).map((result, index) => (
                <FormIndicator key={index} result={result} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Individual League Statistics */}
      {showAllLeagues && leagueStats.length > 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {leagueStats.map((stats, index) => (
            <div key={stats.league?.id || index} className="p-4 border rounded">
              <div className="flex items-center gap-2 mb-3">
                {stats.league?.logo && (
                  <img
                    src={stats.league.logo}
                    alt={stats.league.name}
                    className="w-6 h-6"
                  />
                )}
                <h3 className="font-semibold">
                  {stats.league?.name || `League ${index + 1}`}
                </h3>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p>Played: {stats.fixtures?.played?.total || 0}</p>
                  <p>Wins: {stats.fixtures?.wins?.total || 0}</p>
                  <p>Draws: {stats.fixtures?.draws?.total || 0}</p>
                  <p>Losses: {stats.fixtures?.loses?.total || 0}</p>
                </div>
                <div>
                  <p>Goals For: {stats.goals?.for?.total?.total || 0}</p>
                  <p>
                    Goals Against: {stats.goals?.against?.total?.total || 0}
                  </p>
                  <p>Clean Sheets: {stats.clean_sheet?.total || 0}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TeamStatistics;
