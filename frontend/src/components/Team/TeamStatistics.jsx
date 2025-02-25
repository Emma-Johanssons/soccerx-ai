const TeamStatistics = ({ statistics }) => {
  // Ensure we have default values for all statistics
  const stats = {
    fixtures: {
      played: { total: 0 },
      wins: { total: 0 },
      draws: { total: 0 },
      loses: { total: 0 },
    },
    goals: {
      for: { total: { total: 0 } },
      against: { total: { total: 0 } },
    },
    clean_sheet: { total: 0 },
    ...statistics,
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Team Statistics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Matches</h3>
          <p>Played: {stats.fixtures.played.total}</p>
          <p>Wins: {stats.fixtures.wins.total}</p>
          <p>Draws: {stats.fixtures.draws.total}</p>
          <p>Losses: {stats.fixtures.loses.total}</p>
        </div>
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Goals</h3>
          <p>Scored: {stats.goals.for.total.total}</p>
          <p>Conceded: {stats.goals.against.total.total}</p>
          <p>Clean Sheets: {stats.clean_sheet.total}</p>
        </div>
        {stats.form && (
          <div className="p-4 border rounded">
            <h3 className="font-semibold mb-2">Recent Form</h3>
            <div className="flex gap-1">
              {stats.form
                .slice(-5)
                .split("")
                .map((result, index) => (
                  <div
                    key={index}
                    className={`w-8 h-8 flex items-center justify-center rounded-full font-bold ${
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
    </div>
  );
};

export default TeamStatistics;
