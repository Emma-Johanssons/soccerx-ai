import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, X } from "lucide-react"; // För ikoner (installera med: npm install lucide-react)

const SearchBar = () => {
  const [searchText, setSearchText] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="relative w-full max-w-xl mx-auto px-4 sm:px-0">
      <div className="relative">
        <input
          type="text"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          placeholder="Search for leagues, teams, or players..."
          className="w-full p-3 pl-10 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500 text-sm sm:text-base"
        />
        {loading && (
          <div className="absolute right-3 top-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchBar;
