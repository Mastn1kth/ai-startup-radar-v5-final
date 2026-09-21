import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '../components/Layout';

const navItems = [
  'Dashboard', 'Projects', 'Trends', 'Russia Opportunities',
  'Watchlist', 'Search', 'Clone Specs', 'Reports', 'CIS Opp.', 'Admin',
];

describe('Layout', () => {
  it('renders sidebar with all nav items', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout><div>Content</div></Layout>
      </MemoryRouter>
    );

    navItems.forEach((label) => {
      expect(screen.getByText(label)).toBeDefined();
    });
  });

  it('renders app title and subtitle', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout><div>Content</div></Layout>
      </MemoryRouter>
    );

    expect(screen.getByText('AI Startup Radar')).toBeDefined();
    expect(screen.getByText('2026 Edition')).toBeDefined();
  });

  it('renders children content', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout><div data-testid="child">Child Content</div></Layout>
      </MemoryRouter>
    );

    expect(screen.getByTestId('child')).toBeDefined();
    expect(screen.getByText('Child Content')).toBeDefined();
  });

  it('highlights active route', () => {
    render(
      <MemoryRouter initialEntries={['/projects']}>
        <Layout><div>Content</div></Layout>
      </MemoryRouter>
    );

    const projectsLink = screen.getByText('Projects').closest('a');
    expect(projectsLink?.className).toContain('bg-blue-600');
  });

  it('does not highlight inactive routes', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout><div>Content</div></Layout>
      </MemoryRouter>
    );

    const searchLink = screen.getByText('Search').closest('a');
    expect(searchLink?.className).not.toContain('bg-blue-600');
  });

  it('renders system status in header', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Layout><div>Content</div></Layout>
      </MemoryRouter>
    );

    expect(screen.getByText(/Система активна/)).toBeDefined();
  });
});
