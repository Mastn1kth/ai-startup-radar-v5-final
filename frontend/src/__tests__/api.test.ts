import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockApi),
  },
}));

import '../services/api';

describe('API Service', () => {
  it('creates api instance with correct baseURL', () => {
    expect(axios.create).toHaveBeenCalled();
    const callArgs = (axios.create as any).mock.calls[0][0];
    expect(callArgs.baseURL).toBeDefined();
    expect(callArgs.headers['Content-Type']).toBe('application/json');
    expect(callArgs.timeout).toBe(30000);
  });

  it('request interceptor passes config through', () => {
    const requestUse = mockApi.interceptors.request.use;

    const config = { url: '/test', method: 'GET' as const };
    const interceptorFn = requestUse.mock.calls[0][0];
    const result = interceptorFn(config);
    expect(result).toBe(config);
  });

  it('response interceptor adds userMessage on error', () => {
    const responseUse = mockApi.interceptors.response.use;

    const error = {
      message: 'Test error',
      response: {
        status: 400,
        data: { detail: 'Validation failed' },
      },
    };
    const errorFn = responseUse.mock.calls[0][1];
    expect(errorFn(error)).rejects.toMatchObject({
      userMessage: 'Validation failed',
    });
  });

  it('response interceptor falls back to error message', () => {
    const responseUse = mockApi.interceptors.response.use;

    const error = {
      message: 'Network Error',
      response: undefined,
    };
    const errorFn = responseUse.mock.calls[0][1];
    expect(errorFn(error)).rejects.toMatchObject({
      userMessage: 'Network Error',
    });
  });
});
