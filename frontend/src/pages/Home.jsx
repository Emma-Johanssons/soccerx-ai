import SearchBar from "../components/Search/SearchBar";
import MatchTabs from "../components/Match/MatchTabs";
const Home = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <SearchBar />
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <MatchTabs />
          </div>
        </div>
      </div>
    </div>
  );
};
export default Home;
