// src/pages/AdminPanel.tsx
import React, { useEffect } from "react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";

const AdminPanel: React.FC = () => {
  const { user, handleLogout } = useAuth();
  const navigate = useNavigate();

  // 🚨 Redirect non-admins away
  useEffect(() => {
    if (!user) {
      navigate("/login");
    } else if (user.role !== "admin") {
      navigate("/dashboard");
    }
  }, [user, navigate]);

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-5xl mx-auto bg-white shadow-md rounded-2xl p-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Admin Panel ⚙️
        </h1>
        <p className="text-gray-600 mb-6">
          Manage users, announcements, and system settings here.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-blue-50 rounded-xl shadow hover:shadow-lg cursor-pointer">
            <h2 className="text-lg font-semibold text-blue-700">👥 User Management</h2>
            <p className="text-sm text-gray-600">View and manage user accounts</p>
          </div>

          <div className="p-4 bg-green-50 rounded-xl shadow hover:shadow-lg cursor-pointer">
            <h2 className="text-lg font-semibold text-green-700">📢 Announcements</h2>
            <p className="text-sm text-gray-600">Post and manage announcements</p>
          </div>

          <div className="p-4 bg-purple-50 rounded-xl shadow hover:shadow-lg cursor-pointer">
            <h2 className="text-lg font-semibold text-purple-700">📊 Reports</h2>
            <p className="text-sm text-gray-600">View audit logs and system reports</p>
          </div>

          <div className="p-4 bg-red-50 rounded-xl shadow hover:shadow-lg cursor-pointer">
            <h2 className="text-lg font-semibold text-red-700">⚙️ Settings</h2>
            <p className="text-sm text-gray-600">System configurations</p>
          </div>
        </div>

        <div className="mt-8">
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
