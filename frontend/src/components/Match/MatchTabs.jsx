import { useState } from "react";
import MatchList from "./MatchList";

const MatchTabs = () => {
  const [activeTab, setActiveTab] = useState("today");
  const today = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="border-b border-gray-200 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab("today")}
            className={`${
              activeTab === "today"
                ? "border-[#1a2b4b] text-[#1a2b4b]"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Today ({today})
          </button>
          <button
            onClick={() => setActiveTab("completed")}
            className={`${
              activeTab === "completed"
                ? "border-[#1a2b4b] text-[#1a2b4b]"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors`}
          >
            Completed
          </button>
        </nav>
      </div>

      {/* Match List */}
      <MatchList completed={activeTab === "completed"} />
    </div>
  );
};

export default MatchTabs;
