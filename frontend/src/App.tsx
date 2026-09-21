import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Trends from './pages/Trends';
import RussiaOpportunities from './pages/RussiaOpportunities';
import Watchlist from './pages/Watchlist';
import Search from './pages/Search';
import Admin from './pages/Admin';
import CloneSpecs from './pages/CloneSpecs';
import Reports from './pages/Reports';
import CISOpportunities from './pages/CISOpportunities';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 300000,
      staleTime: 60000,
      retry: 2,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/projects/:id" element={<ProjectDetail />} />
              <Route path="/trends" element={<Trends />} />
              <Route path="/russia-opportunities" element={<RussiaOpportunities />} />
              <Route path="/watchlist" element={<Watchlist />} />
              <Route path="/search" element={<Search />} />
              <Route path="/admin" element={<Admin />} />
              <Route path="/clone-specs" element={<CloneSpecs />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/cis-opportunities" element={<CISOpportunities />} />
            </Routes>
          </Layout>
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;
