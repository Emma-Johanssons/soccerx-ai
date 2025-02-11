import { useState, useEffect } from "react";
import axios from "axios";
import { ChevronUpIcon, ChevronDownIcon } from "@heroicons/react/24/outline";

const MatchDetails = ({ matchId, isOpen, onClose }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        console.log("Fetching details for match:", matchId);
        const response = await axios.get(
          `http://localhost:8000/api/matches/${matchId}`
        );

        if (response.data?.data) {
          setDetails(response.data.data);
          console.log("details:", response.data.data);
        } else {
          console.error("No data in response:", response.data);
          setDetails(null);
        }
      } catch (error) {
        console.error("Error fetching match details:", error);
        setDetails(null);
      } finally {
        setLoading(false);
      }
    };

    if (isOpen && matchId) {
      fetchDetails();
    }
  }, [matchId, isOpen]);

  const renderFormationGrid = (lineup) => {
    if (!lineup?.formation || !lineup?.startXI) return null;

    const isHome = lineup.team.id === details.teams.home.id;
    const teamColor = isHome ? "bg-[#a7d8a7]" : "bg-[#a7d8d8]";

    const formationRows = lineup.formation.split("-").map(Number);
    const totalRows = formationRows.length + 1;

    return (
      <div
        className="relative w-full h-[600px] bg-[#0e4123] rounded-lg overflow-hidden"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      >
        {lineup.startXI.map((item, index) => {
          const player = item.player;
          if (!player) return null;

          let row = 0;
          let position = index;
          let playersInRow = 1;

          if (index === 0) {
            row = 0;
            playersInRow = 1;
          } else {
            let currentRow = 0;
            let positionCount = 1;

            for (let i = 0; i < formationRows.length; i++) {
              if (position < positionCount + formationRows[i]) {
                row = i + 1;
                playersInRow = formationRows[i];
                position = position - positionCount;
                break;
              }
              positionCount += formationRows[i];
            }
          }

          // Styling lineup part: Calculate positions with better centering
          const topPercentage = (row * 120) / (totalRows + 1) + 10;

          let leftPercentage;
          if (playersInRow === 1) {
            leftPercentage = 50;
          } else if (playersInRow === 2) {
            leftPercentage = position === 0 ? 30 : 70;
          } else if (playersInRow === 3) {
            leftPercentage = 20 + position * 30;
          } else if (playersInRow === 4) {
            leftPercentage = 15 + position * 23.33;
          }

          return (
            <div
              key={index}
              className="absolute flex flex-col items-center"
              style={{
                top: `${topPercentage}%`,
                left: `${leftPercentage}%`,
                transform: "translate(-50%, -50%)",
              }}
            >
              <div
                className={`w-12 h-12 ${teamColor} rounded-full flex items-center justify-center text-base font-bold border-2 border-white shadow-md`}
              >
                {player.number}
              </div>
              <div className="text-white text-sm font-medium mt-3 whitespace-nowrap text-center">
                {player.name}
              </div>
            </div>
          );
        })}

        {/* Formation label */}
        <div className="absolute top-4 left-4 bg-black/50 text-white text-sm px-2 py-1 rounded">
          Formation: {lineup.formation}
        </div>
      </div>
    );
  };

  const renderMatchEvents = (events) => {
    if (!events) return null;

    // Split events by team
    const team1Events = events.filter(
      (event) => event.team.id === details.teams.home.id
    );
    const team2Events = events.filter(
      (event) => event.team.id === details.teams.away.id
    );

    const renderTeamEvents = (teamEvents, team) => (
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <img
            src={team.logo}
            alt={team.name}
            className="w-8 h-8 object-contain"
          />
          <h3 className="text-lg font-semibold">{team.name}</h3>
        </div>

        <div className="space-y-2">
          {teamEvents.map((event, index) => (
            <div
              key={index}
              className="flex items-center gap-3 bg-gray-50 rounded-lg p-3"
            >
              {/* Time */}
              <div className="text-lg font-bold text-gray-500 w-12">
                {event.time.elapsed}'
              </div>

              {/* Event icon */}
              <div className="text-xl">
                {event.type === "Goal" && "⚽"}
                {event.type === "Card" &&
                  (event.detail === "Yellow Card" ? "🟨" : "🟥")}
                {event.type === "subst" && "🔄"}
              </div>

              {/* Event details */}
              <div className="flex-1">
                <div className="font-medium">{event.player.name}</div>
                {event.type === "Goal" && event.assist?.name && (
                  <div className="text-sm text-gray-500">
                    Assist: {event.assist.name}
                  </div>
                )}
                {event.type === "subst" && (
                  <div className="text-sm text-gray-500">
                    ↑ {event.assist.name}
                  </div>
                )}
                {event.type === "Card" && (
                  <div className="text-sm text-gray-500">{event.detail}</div>
                )}
              </div>
            </div>
          ))}
          {teamEvents.length === 0 && (
            <div className="text-gray-500 italic text-sm">No events</div>
          )}
        </div>
      </div>
    );

    return (
      <div className="mb-8">
        <h2 className="text-xl font-bold mb-6">Match Events</h2>
        <div className="grid grid-cols-2 gap-8">
          {renderTeamEvents(team1Events, details.teams.home)}
          {renderTeamEvents(team2Events, details.teams.away)}
        </div>
      </div>
    );
  };

  // Add this helper function to format goal scorers
  const formatGoalScorers = (events, teamId) => {
    const goals = events
      .filter((event) => event.type === "Goal" && event.team.id === teamId)
      .map((event) => ({
        name: event.player.name.split(" ").pop(), // Only show last name
        time: event.time.elapsed,
      }));

    return goals.map((goal) => `${goal.name} ${goal.time}'`).join(", ");
  };

  if (!isOpen) return null;
  if (loading)
    return <div className="p-4 text-center">Loading match details...</div>;
  if (!details)
    return <div className="p-4 text-center">No match details available</div>;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] overflow-y-auto">
        {/* Close button */}
        <div className="sticky top-0 bg-white p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-bold">Match Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>

        <div className="p-6">
          {/* Match Header */}
          <div className="mb-8">
            <div className="text-center text-sm text-gray-600 mb-6">
              {details.fixture.date &&
                new Date(details.fixture.date).toLocaleDateString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
            </div>

            <div className="grid grid-cols-3 items-center gap-4">
              {/* Home Team */}
              <div className="text-right">
                <div className="flex items-center justify-end gap-4 mb-2">
                  <div>
                    <div className="font-bold text-xl">
                      {details.teams.home.name}
                    </div>
                  </div>
                  <img
                    src={details.teams.home.logo}
                    alt={details.teams.home.name}
                    className="w-12 h-12 object-contain"
                  />
                </div>
                <div className="text-sm text-gray-600">
                  {formatGoalScorers(
                    details.events || [],
                    details.teams.home.id
                  )}
                </div>
              </div>

              {/* Score */}
              <div className="text-center">
                <div className="flex items-center justify-center gap-4">
                  <div className="text-4xl font-bold">{details.goals.home}</div>
                  <div className="text-gray-400 text-2xl">-</div>
                  <div className="text-4xl font-bold">{details.goals.away}</div>
                </div>
                <div className="text-sm text-gray-500 mt-2">
                  {details.fixture.status.long === "Match Finished" ||
                  details.fixture.status.short === "FT" ||
                  details.fixture.status.short === "END" ||
                  details.fixture.status.short === "AET" ||
                  details.fixture.status.short === "PEN"
                    ? "Full Time"
                    : details.fixture.status.elapsed > 90
                    ? `${details.fixture.status.elapsed}' (ET)`
                    : details.fixture.status.long === "Halftime"
                    ? "Half Time"
                    : details.fixture.status.elapsed
                    ? `${details.fixture.status.elapsed}'`
                    : details.fixture.status.long}
                </div>
              </div>

              {/* Away Team */}
              <div className="text-left">
                <div className="flex items-center justify-start gap-4 mb-2">
                  <img
                    src={details.teams.away.logo}
                    alt={details.teams.away.name}
                    className="w-12 h-12 object-contain"
                  />
                  <div>
                    <div className="font-bold text-xl">
                      {details.teams.away.name}
                    </div>
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  {formatGoalScorers(
                    details.events || [],
                    details.teams.away.id
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Match Events Timeline */}
          {details.events && renderMatchEvents(details.events)}

          {/* Formations and Team Details */}
          {details.lineups && details.lineups.length > 0 && (
            <div>
              <h2 className="text-xl font-bold mb-6 pb-2 border-b border-gray-200">
                Lineups
              </h2>
              <div className="grid grid-cols-2 gap-8">
                {details.lineups.map((lineup, index) => (
                  <div key={index}>
                    {/* Team Name and Formation */}
                    <div className="text-center mb-4">
                      <h3 className="font-bold text-lg">{lineup.team.name}</h3>
                      <p className="text-sm text-gray-600">
                        Formation: {lineup.formation}
                      </p>
                    </div>

                    {/* Formation Grid */}
                    <div className="border border-gray-200 rounded-lg overflow-hidden mb-6">
                      {renderFormationGrid(lineup)}
                    </div>

                    {/* Coach */}
                    <div className="mb-4">
                      <h4 className="font-semibold mb-2">Coach</h4>
                      <div className="text-sm">{lineup.coach.name}</div>
                    </div>

                    {/* Starting XI */}
                    <div className="mb-4">
                      <h4 className="font-semibold mb-2">Starting XI</h4>
                      <div className=" gap-2">
                        {lineup.startXI?.map((player, playerIndex) => (
                          <div
                            key={playerIndex}
                            className="flex items-center gap-2 text-sm"
                          >
                            <span className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center font-medium">
                              {player.player.number}
                            </span>
                            <span>{player.player.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Substitutes */}
                    <div className="mb-4">
                      <h4 className="font-semibold mb-2">Substitutes</h4>
                      <div className=" gap-2">
                        {lineup.substitutes?.map((sub, subIndex) => (
                          <div
                            key={subIndex}
                            className="flex items-center gap-2 text-sm"
                          >
                            <span className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center font-medium">
                              {sub.player.number}
                            </span>
                            <span>{sub.player.name}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatchDetails;
