import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react"; // För ikoner (installera med: npm install lucide-react)

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-[#1a2b4b] border-b border-blue-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <Link
            to="/"
            className="text-white font-bold text-xl hover:text-gray-200 transition-colors"
          >
            <h1>SoccerX</h1>
          </Link>

          {/* Desktop Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <button className="bg-transparent text-white border border-white hover:bg-white hover:text-[#1a2b4b] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200">
              Sign In
            </button>
            <button className="bg-white text-[#1a2b4b] hover:bg-[#e5e7eb] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200">
              Get Started
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden text-white focus:outline-none"
            aria-label={isOpen ? "Close menu" : "Open menu"}
          >
            {isOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {isOpen && (
        <div className="md:hidden bg-[#1a2b4b] border-t border-blue-900">
          <div className="flex flex-col items-center space-y-2 py-4">
            <button className="bg-transparent text-white border border-white hover:bg-white hover:text-[#1a2b4b] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 w-4/5">
              Sign In
            </button>
            <button className="bg-white text-[#1a2b4b] hover:bg-[#e5e7eb] px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 w-4/5">
              Get Started
            </button>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
