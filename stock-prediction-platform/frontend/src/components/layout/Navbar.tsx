"use client";
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, User as UserIcon, Bell, LogOut, Wallet, Sparkles } from 'lucide-react';
import { AuthService } from '@/services/api';
import Link from 'next/link';

export default function Navbar() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [user, setUser] = useState<{
    full_name?: string;
    virtual_balance?: number;
    is_guest?: boolean;
    email?: string;
  } | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const loadUserProfile = async () => {
    try {
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
      const token = localStorage.getItem('token');
      if (token) {
        const profile = await AuthService.fetchProfile();
        setUser(profile);
        localStorage.setItem('user', JSON.stringify(profile));
      }
    } catch (err) {
      // User might be unauthenticated or guest session expired
    }
  };

  useEffect(() => {
    loadUserProfile();

    const handleUpdate = () => {
      loadUserProfile();
    };

    window.addEventListener('portfolio-updated', handleUpdate);
    window.addEventListener('auth-changed', handleUpdate);

    return () => {
      window.removeEventListener('portfolio-updated', handleUpdate);
      window.removeEventListener('auth-changed', handleUpdate);
    };
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const term = searchTerm.trim();
    if (!term) return;

    if (/^[A-Za-z0-9.-]{1,8}$/.test(term)) {
      router.push(`/stock/${term.toUpperCase()}`);
    } else {
      router.push('/search');
    }
  };

  const handleLogout = () => {
    AuthService.logout();
    setUser(null);
    setDropdownOpen(false);
    window.dispatchEvent(new Event('auth-changed'));
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-40 bg-[#0a0a0f]/80 backdrop-blur-lg border-b border-white/10 w-full h-16">
      <div className="flex h-full items-center justify-between px-6">
        {/* Left: Mobile Menu Toggle / Status */}
        <div className="flex flex-1 items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-teal-500"></span>
            </span>
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Market Live</span>
          </div>
        </div>

        {/* Center: Search */}
        <div className="flex-1 flex justify-center max-w-lg w-full px-4">
          <form onSubmit={handleSearch} className="relative w-full group">
            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
            </div>
            <input 
              type="text" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search any ticker (e.g. AAPL, NVDA, TSLA)..." 
              className="w-full bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all font-medium"
            />
          </form>
        </div>

        {/* Right: Actions & Profile */}
        <div className="flex flex-1 items-center justify-end gap-5">
          {user ? (
            <div className="relative">
              <div 
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-3 pl-4 border-l border-white/10 cursor-pointer select-none"
              >
                <div className="flex flex-col items-end hidden md:flex">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-bold text-white max-w-[140px] truncate">
                      {user.full_name || user.email?.split('@')[0] || 'Trader'}
                    </span>
                    {user.is_guest && (
                      <span className="px-1.5 py-0.5 bg-amber-500/20 text-amber-300 text-[10px] font-extrabold rounded">
                        GUEST
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-teal-400 font-mono font-bold flex items-center gap-1">
                    <Wallet className="w-3 h-3 inline" />
                    ${(user.virtual_balance ?? 100000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-500 to-teal-400 p-[2px]">
                  <div className="h-full w-full rounded-full bg-[#0a0a0f] flex items-center justify-center">
                    <UserIcon className="h-5 w-5 text-gray-200 hover:text-white transition-colors"/>
                  </div>
                </div>
              </div>

              {dropdownOpen && (
                <div className="absolute right-0 mt-3 w-64 bg-[#11131f] border border-white/10 rounded-2xl shadow-2xl py-2 z-50 backdrop-blur-2xl">
                  <div className="px-4 py-3 border-b border-white/10">
                    <p className="text-xs text-gray-400">Signed in as</p>
                    <p className="text-sm font-bold text-white truncate">{user.email || 'guest@demo.local'}</p>
                    <div className="mt-2 p-2 bg-white/5 rounded-xl">
                      <div className="text-[11px] text-gray-400">Virtual Buying Power</div>
                      <div className="text-base font-bold text-teal-400 font-mono">
                        ${(user.virtual_balance ?? 100000).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                    </div>
                  </div>

                  <Link
                    href="/dashboard"
                    onClick={() => setDropdownOpen(false)}
                    className="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-300 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <Wallet className="w-4 h-4 text-indigo-400" />
                    Portfolio & Deposit Funds
                  </Link>

                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="text-xs font-bold text-gray-300 hover:text-white px-3 py-1.5 rounded-lg border border-white/10 hover:border-white/20 transition-all"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition-all shadow-[0_0_12px_rgba(79,70,229,0.4)]"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
