const Navbar = () => {
  return (
    <nav className="bg-[#1a2b4b] border-b border-blue-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="text-white font-bold text-xl">SoccerX</div>
          </div>
          <div className="flex items-center space-x-4">
            {/* Sign In Button */}
            <button className="bg-transparent text-white border border-white hover:bg-white hover:text-[#1a2b4b] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200">
              Sign In
            </button>

            {/* Get Started Button */}
            <button className="bg-white text-[#1a2b4b] hover:bg-[#e5e7eb] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200">
              Get Started
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
