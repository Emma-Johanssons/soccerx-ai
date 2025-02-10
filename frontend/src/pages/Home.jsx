import SearchBar from "../components/Search/SearchBar";
import MatchTabs from "../components/Match/MatchTabs";
const Home = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <h1>SoccerX</h1>
      <SearchBar />
      <MatchTabs />
    </div>
  );
};
export default Home;
