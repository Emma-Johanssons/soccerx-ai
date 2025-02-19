const TeamStatistics = ({ statistics }) => {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-2xl font-bold mb-4">Team Statistics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Matches</h3>
          <p>Played: {statistics.matches_played}</p>
          <p>Wins: {statistics.wins}</p>
          <p>Draws: {statistics.draws}</p>
          <p>Losses: {statistics.losses}</p>
        </div>
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Goals For</h3>
          <p>Home: {statistics.goals_for_home}</p>
          <p>Away: {statistics.goals_for_away}</p>
          <p>Total: {statistics.goals_for_total}</p>
        </div>
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Goals Against</h3>
          <p>Home: {statistics.goals_against_home}</p>
          <p>Away: {statistics.goals_against_away}</p>
          <p>Total: {statistics.goals_against_total}</p>
        </div>
        <div className="p-4 border rounded">
          <h3 className="font-semibold mb-2">Clean Sheets</h3>
          <p>Home: {statistics.clean_sheets_home}</p>
          <p>Away: {statistics.clean_sheets_away}</p>
          <p>Total: {statistics.clean_sheets_total}</p>
        </div>
      </div>
    </div>
  );
};

export default TeamStatistics;
