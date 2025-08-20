// src/pages/Dashboard.tsx
import React from "react";
import { useAuth } from "../hooks/useAuth";

const Dashboard: React.FC = () => {
  const { user, handleLogout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-4xl mx-auto bg-white shadow-md rounded-2xl p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Welcome, {user?.name || "Guest"} 👋
        </h1>
        <p className="text-gray-600 mb-6">
          This is your dashboard. From here, you can manage your profile,
          view announcements, and access different features based on your role.
        </p>

        <div className="flex gap-4">
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600"
          >
            Logout
          </button>

          <button
            className="px-4 py-2 bg-blue-500 text-white rounded-lg shadow hover:bg-blue-600"
          >
            View Profile
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
