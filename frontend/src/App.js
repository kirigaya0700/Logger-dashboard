import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { 
  Calendar, 
  User, 
  Clock, 
  TrendingUp, 
  Bell, 
  LogOut, 
  Plus, 
  Download,
  Filter,
  MessageSquare,
  BarChart3,
  Users
} from 'lucide-react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import ReactMarkdown from 'react-markdown';
import { format, parseISO, subDays } from 'date-fns';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Validate token by making a request to get user data instead of notifications
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    setLoading(true);
    try {
      // First try to get user data from localStorage
      const userData = JSON.parse(localStorage.getItem('user') || '{}');
      console.log('Loading user data from localStorage:', userData);
      
      // If we have valid user data, set it immediately
      if (userData && userData.role && userData.id) {
        setUser(userData);
        console.log('User role set to:', userData.role);
      }
      
      // Then validate token by making a request to notifications
      const response = await axios.get(`${API}/notifications`);
      
      // If the request succeeds and we don't have user data, something is wrong
      if (!userData || !userData.role || !userData.id) {
        console.error('Token is valid but user data is missing from localStorage:', userData);
        logout();
      }
    } catch (error) {
      console.error('Token validation failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (tokenData) => {
    console.log('Login called with tokenData:', tokenData);
    setToken(tokenData.access_token);
    setUser(tokenData.user);
    localStorage.setItem('token', tokenData.access_token);
    localStorage.setItem('user', JSON.stringify(tokenData.user));
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
    console.log('User set after login:', tokenData.user);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setLoading(false);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!token && !!user, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

// Components
function LoginForm() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: 'developer',
    manager_id: ''
  });
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  useEffect(() => {
    if (!isLogin) {
      fetchManagers();
    }
  }, [isLogin]);

  const fetchManagers = async () => {
    try {
      const response = await axios.get(`${API}/users/managers`);
      setManagers(response.data);
    } catch (error) {
      console.error('Error fetching managers:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { username: formData.username, password: formData.password }
        : formData;

      const response = await axios.post(`${API}${endpoint}`, payload);
      login(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            {isLogin ? 'Sign in to DevLog' : 'Create your DevLog account'}
          </h2>
        </div>
        <form className="mt-8 space-y-6 bg-white p-8 rounded-lg shadow-lg" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div>
            <input
              name="username"
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
            />
          </div>

          {!isLogin && (
            <>
              <div>
                <input
                  name="email"
                  type="email"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>

              <div>
                <select
                  name="role"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.role}
                  onChange={handleChange}
                >
                  <option value="developer">Developer</option>
                  <option value="manager">Manager</option>
                </select>
              </div>

              {formData.role === 'developer' && (
                <div>
                  <select
                    name="manager_id"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.manager_id}
                    onChange={handleChange}
                  >
                    <option value="">Select a Manager (Optional)</option>
                    {managers.map((manager) => (
                      <option key={manager.id} value={manager.id}>
                        {manager.username} ({manager.email})
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}

          <div>
            <input
              name="password"
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-600 hover:text-blue-500"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Navigation() {
  const { user, logout } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, read: true } : n
      ));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            <span className="ml-2 text-xl font-bold text-gray-900">DevLog</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-gray-600 hover:text-gray-900"
              >
                <Bell className="h-6 w-6" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full text-xs w-5 h-5 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>
              
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg py-1 z-50 border">
                  <div className="px-4 py-2 border-b">
                    <h3 className="text-sm font-medium text-gray-900">Notifications</h3>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-3 text-sm text-gray-500">No notifications</div>
                    ) : (
                      notifications.map((notification) => (
                        <div
                          key={notification.id}
                          className={`px-4 py-3 hover:bg-gray-50 cursor-pointer ${
                            !notification.read ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => markAsRead(notification.id)}
                        >
                          <p className="text-sm text-gray-900">{notification.message}</p>
                          <p className="text-xs text-gray-500 mt-1">
                            {format(parseISO(notification.created_at), 'MMM d, yyyy HH:mm')}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <User className="h-5 w-5 text-gray-600" />
              <span className="text-sm text-gray-700">{user?.username}</span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                {user?.role}
              </span>
            </div>
            
            <button
              onClick={logout}
              className="flex items-center space-x-1 text-gray-600 hover:text-gray-900"
            >
              <LogOut className="h-5 w-5" />
              <span className="text-sm">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

function DeveloperDashboard() {
  const [logs, setLogs] = useState([]);
  const [showLogForm, setShowLogForm] = useState(false);
  const [productivityData, setProductivityData] = useState([]);
  const [editingLog, setEditingLog] = useState(null);

  useEffect(() => {
    fetchLogs();
    fetchProductivityData();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/logs`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const fetchProductivityData = async () => {
    try {
      const response = await axios.get(`${API}/analytics/productivity?days=30`);
      setProductivityData(response.data);
    } catch (error) {
      console.error('Error fetching productivity data:', error);
    }
  };

  const exportData = async () => {
    try {
      const startDate = format(subDays(new Date(), 30), 'yyyy-MM-dd');
      const endDate = format(new Date(), 'yyyy-MM-dd');
      const response = await axios.get(`${API}/analytics/export?start_date=${startDate}&end_date=${endDate}`);
      
      // Create and download CSV file
      const blob = new Blob([response.data.csv_data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `productivity-export-${startDate}-to-${endDate}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  const chartData = {
    labels: productivityData.map(d => format(parseISO(d.date), 'MMM d')),
    datasets: [
      {
        label: 'Hours Worked',
        data: productivityData.map(d => d.total_time),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Mood (1-5)',
        data: productivityData.map(d => d.mood),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1,
        yAxisID: 'y1',
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Productivity Trends (Last 30 Days)',
      },
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          drawOnChartArea: false,
        },
      },
    },
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Developer Dashboard</h1>
        <div className="flex space-x-4">
          <button
            onClick={exportData}
            className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => setShowLogForm(true)}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            <span>New Log</span>
          </button>
        </div>
      </div>

      {/* Productivity Chart */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <Line data={chartData} options={chartOptions} />
      </div>

      {/* Recent Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Recent Logs</h2>
        </div>
        <div className="divide-y">
          {logs.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No logs yet. Create your first daily log!
            </div>
          ) : (
            logs.map((log) => (
              <LogEntry 
                key={log.id} 
                log={log} 
                onEdit={() => setEditingLog(log)}
                onUpdate={fetchLogs}
              />
            ))
          )}
        </div>
      </div>

      {/* Log Form Modal */}
      {(showLogForm || editingLog) && (
        <LogForm
          log={editingLog}
          onClose={() => {
            setShowLogForm(false);
            setEditingLog(null);
          }}
          onSuccess={() => {
            setShowLogForm(false);
            setEditingLog(null);
            fetchLogs();
            fetchProductivityData();
          }}
        />
      )}
    </div>
  );
}

function LogEntry({ log, onEdit, onUpdate }) {
  const totalTasks = log.tasks.length;
  const completedTasks = log.tasks.filter(t => t.completed).length;

  const getMoodEmoji = (mood) => {
    const emojis = ['😢', '😕', '😐', '😊', '😄'];
    return emojis[mood - 1] || '😐';
  };

  return (
    <div className="px-6 py-4 hover:bg-gray-50">
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <div className="flex items-center space-x-4 mb-2">
            <span className="text-lg font-medium text-gray-900">
              {format(parseISO(log.date), 'EEEE, MMMM d, yyyy')}
            </span>
            <span className="text-2xl">{getMoodEmoji(log.mood)}</span>
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="h-4 w-4 mr-1" />
              {log.total_time}h
            </div>
            <div className="text-sm text-gray-500">
              {completedTasks}/{totalTasks} tasks completed
            </div>
          </div>
          
          <div className="space-y-2">
            {log.tasks.map((task, index) => (
              <div key={index} className="flex items-start space-x-2">
                <div className={`w-2 h-2 rounded-full mt-2 ${task.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
                <div className="flex-1">
                  <div className="text-sm text-gray-700 prose prose-sm">
                    <ReactMarkdown>{task.description}</ReactMarkdown>
                  </div>
                  <span className="text-xs text-gray-500">{task.time_spent}h</span>
                </div>
              </div>
            ))}
          </div>

          {log.blockers && (
            <div className="mt-3 p-2 bg-red-50 rounded">
              <span className="text-sm font-medium text-red-800">Blockers:</span>
              <p className="text-sm text-red-700 mt-1">{log.blockers}</p>
            </div>
          )}

          {log.feedback && (
            <div className="mt-3 p-3 bg-blue-50 rounded">
              <div className="flex items-center space-x-2 mb-1">
                <MessageSquare className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Manager Feedback</span>
              </div>
              <p className="text-sm text-blue-700">{log.feedback}</p>
            </div>
          )}
        </div>
        
        <button
          onClick={onEdit}
          className="ml-4 text-blue-600 hover:text-blue-800 text-sm"
        >
          Edit
        </button>
      </div>
    </div>
  );
}

function LogForm({ log, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    date: log ? log.date : format(new Date(), 'yyyy-MM-dd'),
    tasks: log ? log.tasks : [{ description: '', time_spent: 0, completed: true }],
    mood: log ? log.mood : 3,
    blockers: log ? log.blockers : ''
  });
  const [loading, setLoading] = useState(false);

  const addTask = () => {
    setFormData({
      ...formData,
      tasks: [...formData.tasks, { description: '', time_spent: 0, completed: true }]
    });
  };

  const updateTask = (index, field, value) => {
    const updatedTasks = formData.tasks.map((task, i) => 
      i === index ? { ...task, [field]: value } : task
    );
    setFormData({ ...formData, tasks: updatedTasks });
  };

  const removeTask = (index) => {
    const updatedTasks = formData.tasks.filter((_, i) => i !== index);
    setFormData({ ...formData, tasks: updatedTasks });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const totalTime = formData.tasks.reduce((sum, task) => sum + parseFloat(task.time_spent || 0), 0);
      const payload = { ...formData, total_time: totalTime };

      if (log) {
        await axios.put(`${API}/logs/${log.id}`, payload);
      } else {
        await axios.post(`${API}/logs`, payload);
      }
      
      onSuccess();
    } catch (error) {
      console.error('Error saving log:', error);
      alert(error.response?.data?.detail || 'Error saving log');
    } finally {
      setLoading(false);
    }
  };

  const totalTime = formData.tasks.reduce((sum, task) => sum + parseFloat(task.time_spent || 0), 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-screen overflow-y-auto">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {log ? 'Edit Daily Log' : 'New Daily Log'}
          </h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
            <input
              type="date"
              value={formData.date}
              onChange={(e) => setFormData({ ...formData, date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mood (1-5)
            </label>
            <div className="flex space-x-2">
              {[1, 2, 3, 4, 5].map((mood) => (
                <button
                  key={mood}
                  type="button"
                  onClick={() => setFormData({ ...formData, mood })}
                  className={`w-10 h-10 rounded-full text-lg ${
                    formData.mood === mood 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 hover:bg-gray-300'
                  }`}
                >
                  {['😢', '😕', '😐', '😊', '😄'][mood - 1]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Tasks (Total: {totalTime.toFixed(1)}h)
              </label>
              <button
                type="button"
                onClick={addTask}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                + Add Task
              </button>
            </div>
            
            <div className="space-y-3">
              {formData.tasks.map((task, index) => (
                <div key={index} className="border rounded-md p-3">
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={task.completed}
                      onChange={(e) => updateTask(index, 'completed', e.target.checked)}
                      className="mt-1"
                    />
                    <div className="flex-1 space-y-2">
                      <textarea
                        value={task.description}
                        onChange={(e) => updateTask(index, 'description', e.target.value)}
                        placeholder="Task description (markdown supported)"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows="2"
                        required
                      />
                      <input
                        type="number"
                        step="0.1"
                        value={task.time_spent}
                        onChange={(e) => updateTask(index, 'time_spent', e.target.value)}
                        placeholder="Hours spent"
                        className="w-32 px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeTask(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Blockers (Optional)
            </label>
            <textarea
              value={formData.blockers}
              onChange={(e) => setFormData({ ...formData, blockers: e.target.value })}
              placeholder="Any blockers or challenges faced today..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : (log ? 'Update Log' : 'Create Log')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ManagerDashboard() {
  const [teamLogs, setTeamLogs] = useState([]);
  const [developers, setDevelopers] = useState([]);
  const [filters, setFilters] = useState({
    developer_id: '',
    start_date: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd'),
    has_blockers: '',
    reviewed_status: ''
  });
  const [feedbackForm, setFeedbackForm] = useState({ logId: '', text: '' });

  useEffect(() => {
    fetchTeamLogs();
    fetchDevelopers();
  }, [filters]);

  const fetchTeamLogs = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.developer_id) params.append('developer_id', filters.developer_id);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      const response = await axios.get(`${API}/team/logs?${params}`);
      setTeamLogs(response.data);
    } catch (error) {
      console.error('Error fetching team logs:', error);
    }
  };

  const fetchDevelopers = async () => {
    try {
      const response = await axios.get(`${API}/team/developers`);
      setDevelopers(response.data);
    } catch (error) {
      console.error('Error fetching developers:', error);
    }
  };

  const submitFeedback = async (logId, feedbackText) => {
    try {
      await axios.post(`${API}/feedback`, {
        log_id: logId,
        feedback_text: feedbackText
      });
      setFeedbackForm({ logId: '', text: '' });
      fetchTeamLogs(); // Refresh to show feedback
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const exportTeamData = async () => {
    try {
      const params = new URLSearchParams(filters);
      const response = await axios.get(`${API}/analytics/export?${params}`);
      
      const blob = new Blob([response.data.csv_data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `team-productivity-export-${filters.start_date}-to-${filters.end_date}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting team data:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Manager Dashboard</h1>
        <button
          onClick={exportTeamData}
          className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
        >
          <Download className="h-4 w-4" />
          <span>Export Team Data</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <div className="flex items-center space-x-4">
          <Filter className="h-5 w-5 text-gray-500" />
          <span className="font-medium text-gray-700">Filters:</span>
          
          <select
            value={filters.developer_id}
            onChange={(e) => setFilters({ ...filters, developer_id: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Developers</option>
            {developers.map((dev) => (
              <option key={dev.id} value={dev.id}>{dev.username}</option>
            ))}
          </select>
          
          <input
            type="date"
            value={filters.start_date}
            onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          
          <input
            type="date"
            value={filters.end_date}
            onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Team Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Team Size</p>
              <p className="text-2xl font-bold text-gray-900">{developers.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Logs</p>
              <p className="text-2xl font-bold text-gray-900">{teamLogs.length}</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Hours</p>
              <p className="text-2xl font-bold text-gray-900">
                {teamLogs.reduce((sum, log) => sum + log.total_time, 0).toFixed(1)}h
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Team Logs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Team Activity</h2>
        </div>
        <div className="divide-y">
          {teamLogs.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No logs found for the selected criteria.
            </div>
          ) : (
            teamLogs.map((log) => (
              <TeamLogEntry 
                key={log.id} 
                log={log}
                onFeedback={(logId, text) => submitFeedback(logId, text)}
                feedbackForm={feedbackForm}
                setFeedbackForm={setFeedbackForm}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function TeamLogEntry({ log, onFeedback, feedbackForm, setFeedbackForm }) {
  const totalTasks = log.tasks.length;
  const completedTasks = log.tasks.filter(t => t.completed).length;

  const getMoodEmoji = (mood) => {
    const emojis = ['😢', '😕', '😐', '😊', '😄'];
    return emojis[mood - 1] || '😐';
  };

  const showFeedbackForm = feedbackForm.logId === log.id;

  return (
    <div className="px-6 py-4">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-4">
          <span className="font-medium text-blue-600">{log.user_name}</span>
          <span className="text-gray-500">
            {format(parseISO(log.date), 'MMM d, yyyy')}
          </span>
          <span className="text-2xl">{getMoodEmoji(log.mood)}</span>
          <div className="flex items-center text-sm text-gray-500">
            <Clock className="h-4 w-4 mr-1" />
            {log.total_time}h
          </div>
          <div className="text-sm text-gray-500">
            {completedTasks}/{totalTasks} tasks
          </div>
        </div>
        
        <button
          onClick={() => setFeedbackForm({ 
            logId: showFeedbackForm ? '' : log.id, 
            text: log.feedback || '' 
          })}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          {log.feedback ? 'Edit Feedback' : 'Add Feedback'}
        </button>
      </div>

      <div className="space-y-2 mb-4">
        {log.tasks.map((task, index) => (
          <div key={index} className="flex items-start space-x-2">
            <div className={`w-2 h-2 rounded-full mt-2 ${task.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
            <div className="flex-1">
              <div className="text-sm text-gray-700 prose prose-sm">
                <ReactMarkdown>{task.description}</ReactMarkdown>
              </div>
              <span className="text-xs text-gray-500">{task.time_spent}h</span>
            </div>
          </div>
        ))}
      </div>

      {log.blockers && (
        <div className="mb-4 p-2 bg-red-50 rounded">
          <span className="text-sm font-medium text-red-800">Blockers:</span>
          <p className="text-sm text-red-700 mt-1">{log.blockers}</p>
        </div>
      )}

      {log.feedback && !showFeedbackForm && (
        <div className="mb-4 p-3 bg-green-50 rounded">
          <div className="flex items-center space-x-2 mb-1">
            <MessageSquare className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">Your Feedback</span>
          </div>
          <p className="text-sm text-green-700">{log.feedback}</p>
        </div>
      )}

      {showFeedbackForm && (
        <div className="mt-4 p-4 bg-gray-50 rounded">
          <textarea
            value={feedbackForm.text}
            onChange={(e) => setFeedbackForm({ ...feedbackForm, text: e.target.value })}
            placeholder="Add your feedback for this log..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows="3"
          />
          <div className="flex justify-end space-x-2 mt-2">
            <button
              onClick={() => setFeedbackForm({ logId: '', text: '' })}
              className="px-3 py-1 text-sm border border-gray-300 rounded text-gray-700 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={() => onFeedback(log.id, feedbackForm.text)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              disabled={!feedbackForm.text.trim()}
            >
              Submit Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <AuthContent />
      </div>
    </AuthProvider>
  );
}

function AuthContent() {
  const { isAuthenticated, user, loading } = useAuth();

  // Debug logging
  console.log('AuthContent - isAuthenticated:', isAuthenticated, 'user:', user, 'loading:', loading);

  // Show loading state while user data is being fetched
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginForm />;
  }

  // Additional safety check - if we're authenticated but don't have user data, something is wrong
  if (!user || !user.role) {
    console.error('Authenticated but missing user data. Forcing logout.');
    // This will trigger a logout
    return <LoginForm />;
  }

  return (
    <Router>
      <Navigation />
      <Routes>
        <Route 
          path="/" 
          element={
            user.role === 'manager' ? 
            <Navigate to="/manager" replace /> : 
            <Navigate to="/developer" replace />
          } 
        />
        <Route path="/developer" element={
          user.role === 'developer' ? <DeveloperDashboard /> : <Navigate to="/manager" replace />
        } />
        <Route path="/manager" element={
          user.role === 'manager' ? <ManagerDashboard /> : <Navigate to="/developer" replace />
        } />
      </Routes>
    </Router>
  );
}

export default App;
