import { useState, useEffect } from "react";
import axios from "axios";
import { getMatchCommentaryUrl } from "../../config/api";

const LiveCommentary = ({ matchId, matchStatus }) => {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCommentary = async () => {
    if (!matchId) return;

    try {
      const response = await axios.get(getMatchCommentaryUrl(matchId));

      if (response.data?.status === "success") {
        const commentary = response.data.data.commentary;
        setComments(commentary);
      }
    } catch (error) {
      console.error("Error fetching commentary:", error);
      setError("Failed to load commentary");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommentary();

    // Poll for updates if match is live
    const isLive = ["1H", "2H", "HT"].includes(matchStatus);
    let intervalId;

    if (isLive) {
      intervalId = setInterval(fetchCommentary, 30000); // Poll every 30 seconds
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [matchId, matchStatus]);

  if (loading) return <div>Loading commentary...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="live-commentary p-4">
      <h3 className="text-lg font-semibold mb-4">Live Commentary</h3>
      {comments.length === 0 ? (
        <div className="text-gray-500">
          {matchStatus === "NS"
            ? "Commentary will be available when the match starts."
            : "No commentary available yet."}
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div
              key={comment.id}
              className="commentary-item border-l-4 border-blue-500 pl-4"
            >
              <div className="text-sm text-gray-600">{comment.minute}'</div>
              <div className="mt-1">{comment.commentary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LiveCommentary;
