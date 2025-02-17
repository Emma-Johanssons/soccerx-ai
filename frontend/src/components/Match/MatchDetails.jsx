import { useState, useEffect } from "react";
import axios from "axios";
import { ChevronUpIcon, ChevronDownIcon } from "@heroicons/react/24/outline";
import { XMarkIcon } from "@heroicons/react/24/outline";

const MAJOR_LEAGUES = {
  "Premier League": true, // England
  "La Liga": true, // Spain
  "Serie A": true, // Italy
  Bundesliga: true, // Germany
  "Ligue 1": true, // France
  "UEFA Champions League": true,
  "UEFA Europa League": true,
  "UEFA Conference League": true,
};

const MatchDetails = ({ matchId, isOpen, onClose }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lineupAvailable, setLineupAvailable] = useState(false);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setLoading(true);
        const response = await axios.get(
          `http://localhost:8000/api/matches/${matchId}`
        );

        if (response.data?.data) {
          const matchData = response.data.data;
          console.log("Match data:", matchData);

          // Check if this match is from a major league
          const isFromMajorLeague =
            MAJOR_LEAGUES[matchData.league?.name] || false;
          console.log("League name:", matchData.league?.name);
          console.log("Is major league:", isFromMajorLeague);

          setDetails(matchData);

          // Check lineup availability
          const hasLineups =
            matchData.lineups &&
            matchData.lineups.length > 0 &&
            matchData.lineups.some(
              (lineup) => lineup.formation && lineup.startXI?.length > 0
            );

          console.log("Has lineups:", hasLineups);
          setLineupAvailable(hasLineups);
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

    // Parse formation (e.g., "3-4-2-1")
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

          // Calculate positions with better centering
          const topPercentage = (row * 120) / (totalRows + 1) + 10;

          // Adjusted horizontal positioning with slightly larger gaps
          let leftPercentage;
          if (playersInRow === 1) {
            leftPercentage = 50; // Center single player
          } else if (playersInRow === 2) {
            leftPercentage = position === 0 ? 30 : 70; // Increased gap (was 35/65)
          } else if (playersInRow === 3) {
            leftPercentage = 20 + position * 30; // Increased gap (was 25)
          } else if (playersInRow === 4) {
            leftPercentage = 15 + position * 23.33; // Increased gap (was 20)
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

  const formatGoalScorers = (events, teamId) => {
    if (!events || !Array.isArray(events)) return "";

    const goals = events
      .filter((event) => event.type === "Goal" && event.team.id === teamId)
      .map((event) => ({
        name: event.player?.name
          ? event.player.name.split(" ").pop()
          : "Unknown",
        time: event.time?.elapsed || 0,
      }))
      .filter((goal) => goal.name && goal.time); // Filter out any invalid goals

    return goals.map((goal) => `${goal.name} ${goal.time}'`).join(", ");
  };

  const NoLineupsMessage = () => (
    <div className="text-center p-4 bg-gray-50 rounded-lg">
      <p className="text-gray-600 mb-2">Lineup information is not available.</p>
    </div>
  );

  const renderCoaches = (lineup) => {
    if (!lineup?.coach) return null;

    return (
      <div className="mt-4 mb-4">
        <h5 className="font-medium mb-2">Coach</h5>
        <div className="flex items-center gap-3 p-2 bg-white rounded">
          {lineup.coach.name && (
            <>
              {lineup.coach.photo && (
                <img
                  src={lineup.coach.photo}
                  alt={lineup.coach.name}
                  className="w-8 h-8 rounded-full object-cover"
                />
              )}
              <span className="text-sm font-medium">{lineup.coach.name}</span>
            </>
          )}
        </div>
      </div>
    );
  };

  const renderSubstitutions = (lineup) => {
    if (!lineup?.substitutes) return null;

    return (
      <div className="mt-4">
        <h5 className="font-medium mb-2">Substitutes</h5>
        <div className="mb-1">
          {lineup.substitutes.map((sub, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-2 bg-white rounded"
            >
              <div className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-sm">
                {sub.player.number}
              </div>
              <span className="text-sm">{sub.player.name}</span>
              <span className="text-xs text-gray-500 ml-auto">
                {sub.player.pos}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!isOpen) return null;
  if (loading)
    return <div className="p-4 text-center">Loading match details...</div>;
  if (!details)
    return <div className="p-4 text-center">No match details available</div>;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-bold">Match Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>
        <div className="p-6">
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
                  details.fixture.status.short === "AET" || // After Extra Time
                  details.fixture.status.short === "PEN" // Penalties
                    ? "Full Time"
                    : details.fixture.status.elapsed > 90
                    ? `${details.fixture.status.elapsed}' (ET)` // Extra Time
                    : details.fixture.status.long === "Halftime"
                    ? "Half Time"
                    : details.fixture.status.elapsed
                    ? `${details.fixture.status.elapsed}'`
                    : details.fixture.status.long}
                </div>
              </div>

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

          {details.events && renderMatchEvents(details.events)}

          <div className="space-y-6">
            <h3 className="text-lg font-bold">Lineups</h3>
            {lineupAvailable ? (
              <div className="grid md:grid-cols-2 gap-6">
                {details.lineups.map((team, index) => (
                  <div key={index} className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold mb-2">{team.team.name}</h4>

                    {team.startXI && team.startXI.length > 0 && (
                      <div>
                        <h5 className="font-medium mb-2">Starting XI</h5>
                        <div className="border border-gray-200 rounded-lg overflow-hidden mb-6">
                          {renderFormationGrid(team)}
                        </div>
                      </div>
                    )}
                    {renderCoaches(team)}

                    {renderSubstitutions(team)}
                  </div>
                ))}
              </div>
            ) : (
              <NoLineupsMessage />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchDetails;
