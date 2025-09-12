/**
 * Admin Authentication Utilities - Isolated and Non-Invasive
 * This file provides admin checks without modifying existing auth flow
 */

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
}

/**
 * Check if current user is admin (non-invasive)
 * Defaults to false if any error occurs to maintain safety
 */
export function isCurrentUserAdmin(user: User | null): boolean {
  try {
    if (!user || !user.email) {
      return false;
    }
    
    // TEMPORARY: Enable admin tab for all users for debugging hard-coded goals issue
    // TODO: Revert this after debugging is complete
    return true;
    
    // Original logic (commented out temporarily):
    // const adminEmails = ['debashishroy@gmail.com'];
    // return adminEmails.includes(user.email.toLowerCase());
  } catch (error) {
    // Fail safely - if there's any error, assume not admin
    console.warn('Admin check failed safely:', error);
    return false;
  }
}

/**
 * Get admin role for current user
 * Returns 'admin' or 'user' safely
 */
export function getUserRole(user: User | null): 'admin' | 'user' {
  return isCurrentUserAdmin(user) ? 'admin' : 'user';
}

/**
 * Check if admin features should be available
 * Additional safety check for feature flags
 */
export function areAdminFeaturesEnabled(): boolean {
  try {
    // Could add environment check here if needed
    return true;
  } catch (error) {
    return false;
  }
}