import { jwtDecode } from 'jwt-decode';

export const getAccessToken = () => localStorage.getItem('access_token');
export const getRefreshToken = () => localStorage.getItem('refresh_token');

export const setTokens = (accessToken: string, refreshToken: string) => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

export const removeTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const isAuthenticated = () => {
  const token = getAccessToken();
  if (!token) return false;
  
  try {
    const decoded = jwtDecode(token);
    // Check if token is expired
    if (decoded.exp && decoded.exp * 1000 < Date.now()) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
};

export const getUserRole = (): 'student' | 'staff' | null => {
  const token = getAccessToken();
  if (!token) return null;
  
  try {
    const decoded: any = jwtDecode(token);
    return decoded.role || null;
  } catch {
    return null;
  }
};
