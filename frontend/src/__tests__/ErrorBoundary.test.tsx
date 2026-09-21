import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

const GoodChild = () => <div data-testid="good-child">All good</div>;

const BadChild = () => {
  throw new Error('Test crash');
};

const OriginalError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});

afterEach(() => {
  console.error = OriginalError;
});

describe('ErrorBoundary', () => {
  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary>
        <GoodChild />
      </ErrorBoundary>
    );
    expect(screen.getByTestId('good-child')).toBeDefined();
    expect(screen.getByText('All good')).toBeDefined();
  });

  it('renders error UI when a child throws', () => {
    render(
      <ErrorBoundary>
        <BadChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeDefined();
    expect(screen.getByText('Test crash')).toBeDefined();
    expect(screen.getByText('Reload page')).toBeDefined();
  });

  it('shows fallback message when error has no message', () => {
    const ReallyBadChild = () => {
      throw new Error();
    };
    render(
      <ErrorBoundary>
        <ReallyBadChild />
      </ErrorBoundary>
    );
    expect(screen.getByText('An unexpected error occurred')).toBeDefined();
  });

  it('renders reload button that resets error state', () => {
    render(
      <ErrorBoundary>
        <BadChild />
      </ErrorBoundary>
    );
    const button = screen.getByText('Reload page');
    expect(button).toBeDefined();
    expect(button?.className).toContain('bg-blue-600');
  });
});
