"use client";
/* eslint-disable react-hooks/set-state-in-effect */

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

type QueryState<T> = {
  data: T | undefined;
  error: unknown;
  loading: boolean;
  refresh: () => Promise<void>;
};

function shouldRetry(error: unknown) {
  return error instanceof ApiError && (error.status === 0 || error.status >= 500);
}

/** A small shared query primitive for API-backed client components. */
export function useApiQuery<T>(
  query: () => Promise<T>,
  options: { retries?: number } = {},
): QueryState<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<unknown>();
  const [loading, setLoading] = useState(true);
  const retries = options.retries ?? 1;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        const result = await query();
        setData(result);
        setError(undefined);
        setLoading(false);
        return;
      } catch (caught) {
        if (attempt === retries || !shouldRetry(caught)) {
          setError(caught);
          setLoading(false);
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 350 * (attempt + 1)));
      }
    }
  }, [query, retries]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { data, error, loading, refresh };
}

export function useDebouncedValue<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timeout = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timeout);
  }, [value, delay]);
  return debounced;
}
