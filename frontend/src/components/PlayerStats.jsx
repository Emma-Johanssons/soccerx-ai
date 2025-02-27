import React, { useState } from "react";

const formatStat = (value) => {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") {
    if (value % 1 !== 0) return value.toFixed(1);
    return value.toString();
  }
  return value;
};

const isGoalkeeper = (stats) => {
  return (
    stats?.games?.position === "Goalkeeper" ||
    stats?.statistics?.[0]?.games?.position === "Goalkeeper"
  );
};

const aggregatedCareerStats = (careerStats) => {
  if (!careerStats?.seasons) return {};

  let totalSaves = 0;
  let totalConceded = 0;
  let totalCleanSheets = 0;
  let totalAppearances = 0;
  let totalSeasons = careerStats.seasons.length;

  careerStats.seasons.forEach((season) => {
    season.teams.forEach((teamStats) => {
      if (teamStats.games?.appearences) {
        totalAppearances += teamStats.games.appearences;
      }
      if (teamStats.goals?.saves) {
        totalSaves += teamStats.goals.saves;
      }
      if (teamStats.goals?.conceded) {
        totalConceded += teamStats.goals.conceded;
      }
      if (teamStats.goals?.clean_sheets) {
        totalCleanSheets += teamStats.goals.clean_sheets;
      }
    });
  });

  return {
    seasons_played: totalSeasons,
    total_appearances: totalAppearances,
    total_saves: totalSaves,
    total_conceded: totalConceded,
    total_clean_sheets: totalCleanSheets,
  };
};

const StatCard = ({ title, value }) => (
  <div className="bg-gray-50 p-4 rounded-lg">
    <div className="text-sm text-gray-600">{title}</div>
    <div className="text-xl font-semibold mt-1">{value}</div>
  </div>
);

const PlayerStats = ({ currentStats, careerStats }) => {
  const [expandedSeason, setExpandedSeason] = useState(null);

  if (!currentStats && !careerStats) {
    return <div>No statistics available</div>;
  }

  const isGK = isGoalkeeper(currentStats);
  const aggregatedStats = aggregatedCareerStats(careerStats);

  console.log("Aggregated Career Stats:", aggregatedStats);

  return (
    <div className="grid grid-cols-1 gap-4 mt-6">
      {/* Career Overview */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Career Overview</h2>
          <span className="text-sm text-gray-500">Last 5 seasons</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="Seasons" value={aggregatedStats.seasons_played} />
          <StatCard
            title="Appearances"
            value={aggregatedStats.total_appearances}
          />
          {isGK ? (
            <>
              <StatCard title="Saves" value={aggregatedStats.total_saves} />
              <StatCard
                title="Goals Conceded"
                value={aggregatedStats.total_conceded}
              />

              <StatCard
                title="Save Rate"
                value={
                  aggregatedStats.total_saves + aggregatedStats.total_conceded >
                  0
                    ? `${(
                        (aggregatedStats.total_saves /
                          (aggregatedStats.total_saves +
                            aggregatedStats.total_conceded)) *
                        100
                      ).toFixed(1)}%`
                    : "-"
                }
              />
            </>
          ) : (
            <>
              <StatCard title="Goals" value={careerStats?.total_goals || 0} />
              <StatCard
                title="Assists"
                value={careerStats?.total_assists || 0}
              />
            </>
          )}
        </div>
      </div>

      {/* Season History */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Season History</h2>
        {careerStats?.seasons?.map((season) => {
          const teamGroups = {};
          season.teams.forEach((stat) => {
            if (stat.games?.appearences > 0) {
              const teamId = stat.team?.id;
              if (!teamGroups[teamId]) {
                teamGroups[teamId] = [];
              }
              teamGroups[teamId].push(stat);
            }
          });

          return (
            <div key={season.season} className="mb-6">
              <h3
                className="font-semibold text-lg border-b pb-2 cursor-pointer flex items-center justify-between"
                onClick={() =>
                  setExpandedSeason(
                    expandedSeason === season.season ? null : season.season
                  )
                }
              >
                <span>Season {season.season}</span>
                <span>{expandedSeason === season.season ? "−" : "+"}</span>
              </h3>
              {expandedSeason === season.season && (
                <div className="space-y-6 mt-4">
                  {Object.values(teamGroups).map((teamStats, index) => (
                    <div
                      key={`${season.season}_${teamStats[0].team?.id}_${index}`}
                      className="space-y-4"
                    >
                      <div className="font-medium text-lg flex items-center gap-2">
                        <img
                          src={teamStats[0].team?.logo}
                          alt={teamStats[0].team?.name}
                          className="w-6 h-6"
                        />
                        {teamStats[0].team?.name}
                      </div>
                      {teamStats.map((stat, statIndex) => (
                        <div key={statIndex} className="p-4 bg-gray-50 rounded">
                          {renderTeamStats(stat, isGK)}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const renderTeamStats = (teamStats, isGK) => {
  if (!teamStats || !teamStats.team) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-2">
          <img
            src={teamStats.team?.logo}
            alt={teamStats.team?.name}
            className="w-6 h-6"
          />
          <span className="font-medium">{teamStats.team?.name}</span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatCard title="Appearances" value={teamStats.games?.appearences} />
        {isGK ? (
          <>
            <StatCard title="Saves" value={teamStats.goals?.saves || 0} />
            <StatCard
              title="Goals Conceded"
              value={teamStats.goals?.conceded || 0}
            />
          </>
        ) : (
          <>
            <StatCard title="Goals" value={teamStats.goals?.total || 0} />
            <StatCard title="Assists" value={teamStats.goals?.assists || 0} />
          </>
        )}
      </div>
    </div>
  );
};

export default PlayerStats;
