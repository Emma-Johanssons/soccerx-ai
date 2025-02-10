import { useState } from "react";
import MatchList from "./MatchList";

const MatchTabs = () => {
  const [activeTab, setActiveTab] = useState("today");
  const today = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  const [showAllLeagues, setShowAllLeagues] = useState(false);

  return (
    <div className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab("today")}
              className={`${
                activeTab === "today"
                  ? "border-b-2 border-[#1a2b4b] text-[#1a2b4b]"
                  : "border-b-2 border-transparent text-gray-500 hover:text-gray-700"
              } py-4 px-1 text-sm font-medium transition-colors`}
            >
              Today ({today})
            </button>
            <button
              onClick={() => setActiveTab("completed")}
              className={`${
                activeTab === "completed"
                  ? "border-b-2 border-[#1a2b4b] text-[#1a2b4b]"
                  : "border-b-2 border-transparent text-gray-500 hover:text-gray-700"
              } py-4 px-1 text-sm font-medium transition-colors`}
            >
              Completed
            </button>
          </nav>

          <button
            onClick={() => setShowAllLeagues(!showAllLeagues)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {showAllLeagues ? "Show Major Leagues" : "View All Leagues"}
          </button>
        </div>
      </div>

      <div className="px-4 py-6 bg-gray-50">
        <MatchList
          completed={activeTab === "completed"}
          showAllLeagues={showAllLeagues}
        />
      </div>
    </div>
  );
};

export default MatchTabs;
