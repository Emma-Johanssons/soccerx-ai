import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import LeaguePage from "./pages/LeaguePage";
import TeamPage from "./pages/TeamPage";
import PlayerPage from "./pages/PlayerPage";
import SearchResults from "./pages/SearchResults";
import Layout from "./components/Layout/Layout";
import MatchDetails from "./components/Match/MatchDetails";
import Navbar from "./components/Layout/Navbar";

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="/league/:id" element={<LeaguePage />} />
          <Route path="/team/:id" element={<TeamPage />} />
          <Route
            path="/team/:teamId/player/:playerId"
            element={<PlayerPage />}
          />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/match/:matchId" element={<MatchDetails />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
