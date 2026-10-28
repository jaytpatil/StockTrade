"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AuthService } from '@/services/api';
import { Sparkles, Loader2, AlertCircle, ArrowRight } from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [guestLoading, setGuestLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      // Register new user
      await AuthService.signup({
        full_name: fullName,
        email: email,
        password: password
      });

      // Automatically sign in
      await AuthService.login({
        email: email,
        password: password
      });

      window.dispatchEvent(new Event('auth-changed'));
      router.push('/dashboard');
    } catch (err: any) {
      console.error("Registration failed:", err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Registration failed. An account with this email may already exist.');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    setError(null);
    setGuestLoading(true);
    try {
      await AuthService.loginAsGuest();
      window.dispatchEvent(new Event('auth-changed'));
      router.push('/dashboard');
    } catch (err: any) {
      console.error("Guest login failed:", err);
      setError('Could not initialize guest session. Please try again.');
    } finally {
      setGuestLoading(false);
    }
  };

  return (
    <div className="bg-[#0f111a]/80 border border-white/10 p-8 rounded-3xl backdrop-blur-xl shadow-2xl">
      <div className="mb-6">
        <h2 className="text-3xl font-bold mb-2">Create Account</h2>
        <p className="text-gray-400">Get access to live trading signals & $100,000 virtual balance.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Guest Mode Callout */}
      <div className="mb-6 p-4 bg-gradient-to-r from-teal-500/10 to-indigo-500/10 border border-teal-500/20 rounded-2xl">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-bold text-teal-300 text-sm flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-teal-400" /> Instant Demo Mode
            </div>
            <p className="text-xs text-gray-400 mt-0.5">Explore with $100k demo funds in 1-click.</p>
          </div>
          <button
            type="button"
            onClick={handleGuestLogin}
            disabled={guestLoading || loading}
            className="px-4 py-2 bg-teal-500 hover:bg-teal-400 text-black text-xs font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(45,212,191,0.3)] flex items-center gap-1.5 disabled:opacity-50"
          >
            {guestLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            Play as Guest
          </button>
        </div>
      </div>

      <div className="relative flex py-2 items-center mb-4">
        <div className="flex-grow border-t border-white/10"></div>
        <span className="flex-shrink mx-4 text-xs uppercase tracking-wider text-gray-500">Or register new account</span>
        <div className="flex-grow border-t border-white/10"></div>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Full Name</label>
          <input 
            type="text" 
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Jane Doe"
            className="w-full bg-[#0a0a0f] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Email Address</label>
          <input 
            type="email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="trader@example.com"
            className="w-full bg-[#0a0a0f] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1.5">Password</label>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Choose a secure password"
            className="w-full bg-[#0a0a0f] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
            required
          />
        </div>

        <button 
          type="submit" 
          disabled={loading || guestLoading}
          className="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-3 px-4 rounded-xl shadow-[0_0_15px_rgba(45,212,191,0.4)] hover:shadow-[0_0_25px_rgba(45,212,191,0.6)] transition-all mt-4 flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Account'}
          {!loading && <ArrowRight className="w-4 h-4" />}
        </button>
      </form>

      <div className="mt-8 text-center text-sm text-gray-400">
        Already have an account? <Link href="/login" className="text-white hover:text-teal-400 font-medium transition-colors">Sign In</Link>
      </div>
    </div>
  );
}
