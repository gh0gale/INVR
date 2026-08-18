/**
 * Single source for the backend origin. Previously this literal was repeated
 * in four call sites, which made the documented VITE_API_BASE_URL dead config.
 */
export const API_BASE: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiUrl = (path: string): string =>
  `${API_BASE.replace(/\/$/, '')}${path}`;
