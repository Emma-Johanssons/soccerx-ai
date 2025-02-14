import React, { useState } from "react";

const PlayerStats = ({ currentStats, careerStats }) => {
  const [expandedSeason, setExpandedSeason] = useState(null);

  if (!currentStats && !careerStats) {
    return <div>No statistics available</div>;
  }

  const StatBlock = ({ title, stats }) => (
    <div className="p-3 bg-gray-50 rounded">
      <h4 className="font-semibold mb-2">{title}</h4>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {Object.entries(stats).map(([key, value]) => (
          <div key={key}>
            <span className="text-gray-600">{key.replace(/_/g, " ")}: </span>
            <span className="font-medium">{value || 0}</span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      {/* Career Stats */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">
          Career Overview (Last 5 Seasons)
        </h2>
        {careerStats && (
          <div className="space-y-2">
            <div>Seasons Played: {careerStats.seasons_played || 0}</div>
            <div>Total Appearances: {careerStats.total_appearances || 0}</div>
            <div>Total Goals: {careerStats.total_goals || 0}</div>
            <div>Total Assists: {careerStats.total_assists || 0}</div>
          </div>
        )}
      </div>

      {/* Season History */}
      <div className="col-span-1 md:col-span-2 bg-white p-4 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">Season History</h2>
        {careerStats?.seasons?.map((season) => (
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
            {season.teams?.map((teamStats, index) => (
              <div
                key={`${season.season}_${teamStats.team.id}_${index}`}
                className="mt-4 p-4 bg-gray-50 rounded"
              >
                <div className="flex items-center gap-3 mb-3">
                  <img
                    src={teamStats.team.logo}
                    alt={teamStats.team.name}
                    className="w-6 h-6"
                  />
                  <span className="font-medium">{teamStats.team.name}</span>
                  <span className="text-sm text-gray-600">
                    ({teamStats.league.name})
                  </span>
                </div>
                {expandedSeason === season.season ? (
                  <div className="space-y-4">
                    <StatBlock title="Games" stats={teamStats.games} />
                    <StatBlock
                      title="Goals & Assists"
                      stats={teamStats.goals}
                    />
                    <StatBlock title="Shots" stats={teamStats.shots} />
                    <StatBlock title="Passes" stats={teamStats.passes} />
                    <StatBlock title="Tackles" stats={teamStats.tackles} />
                    <StatBlock title="Duels" stats={teamStats.duels} />
                    <StatBlock title="Dribbles" stats={teamStats.dribbles} />
                    <StatBlock title="Fouls" stats={teamStats.fouls} />
                    <StatBlock title="Cards" stats={teamStats.cards} />
                    <StatBlock title="Penalties" stats={teamStats.penalty} />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Appearances</p>
                      <p className="font-bold">
                        {teamStats.games.appearences || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Goals</p>
                      <p className="font-bold">{teamStats.goals.total || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Assists</p>
                      <p className="font-bold">
                        {teamStats.goals.assists || 0}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Minutes</p>
                      <p className="font-bold">
                        {teamStats.games.minutes || 0}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default PlayerStats;
