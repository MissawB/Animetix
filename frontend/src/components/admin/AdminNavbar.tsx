import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Shield, Users, Activity, Clock, Workflow, Target, ListChecks, Coins,
  LayoutDashboard, BarChart3, Database, Brain, Network, ShieldAlert
} from 'lucide-react';

const AdminNavbar: React.FC = () => {
  const location = useLocation();
  
  const navItems = [
    { label: 'Hub', path: '/admin/dashboard/', icon: <LayoutDashboard className="w-4 h-4" /> },
    { label: 'Users', path: '/admin/users/', icon: <Users className="w-4 h-4" /> },
    { label: 'TTC', path: '/admin/ttc-monitoring/', icon: <Clock className="w-4 h-4" /> },
    { label: 'Economics', path: '/admin/economics/', icon: <Coins className="w-4 h-4" /> },
    { label: 'Finances', path: '/admin/financials/', icon: <Coins className="w-4 h-4" /> },
    { label: 'MLOps', path: '/admin/mlops/', icon: <Workflow className="w-4 h-4" /> },
    { label: 'Safety', path: '/admin/safety/', icon: <ShieldAlert className="w-4 h-4" /> },
    { label: 'Observability', path: '/admin/observability/', icon: <Activity className="w-4 h-4" /> },
    { label: 'DSPy', path: '/admin/dspy/', icon: <Target className="w-4 h-4" /> },
    { label: 'Health', path: '/admin/health/', icon: <Activity className="w-4 h-4" /> },
    { label: 'Eval', path: '/admin/eval/', icon: <Brain className="w-4 h-4" /> },
    { label: 'Curation', path: '/admin/curation/', icon: <ListChecks className="w-4 h-4" /> },
    { label: 'Graph', path: '/admin/graph-debugger/', icon: <Network className="w-4 h-4" /> },
    { label: 'SOTA', path: '/admin/sota-benchmark/', icon: <BarChart3 className="w-4 h-4" /> },
    { label: 'Dataset', path: '/admin/gold-dataset/', icon: <Database className="w-4 h-4" /> },
  ];

  return (
    <div className="bg-black/95 dark:bg-[#0a0a1a] backdrop-blur-md border-b border-white/5 py-2 px-6 sticky top-[72px] z-[900] overflow-x-auto no-scrollbar">
      <div className="max-w-7xl mx-auto flex items-center gap-2">
        <div className="flex items-center gap-2 pr-4 border-r border-white/10 mr-2 shrink-0">
          <Shield className="w-4 h-4 text-blue-500" />
          <span className="text-[10px] font-black uppercase tracking-widest text-white/50">Admin <span className="hidden sm:inline">Panel</span></span>
        </div>
        
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link 
                key={item.path} 
                to={item.path} 
                className={`flex items-center gap-2 px-4 py-2 rounded-xl no-underline transition-all shrink-0 ${
                  isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20' 
                  : 'text-white/40 hover:text-white hover:bg-white/5'
                }`}
              >
                {item.icon}
                <span className="text-[10px] font-black uppercase tracking-widest">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AdminNavbar;
