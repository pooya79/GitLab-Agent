# Frontend Authentication System

This directory contains the complete authentication system for the GitLab Agent frontend application.

## 📁 Files Overview

### `tokens.ts`

Core token management utilities that handle localStorage operations.

**Functions:**

- `setAuthTokens(tokens)` - Save access token, refresh token, and expiry time
- `getAccessToken()` - Get the current access token
- `getRefreshToken()` - Get the current refresh token
- `getAuthTokens()` - Get all tokens with calculated expiry
- `clearAuthTokens()` - Remove all tokens (for logout)
- `isTokenExpired(bufferSeconds)` - Check if token is expired (default 60s buffer)
- `isAuthenticated()` - Quick check if user has valid tokens
- `getTimeUntilExpiry()` - Get remaining time in seconds

### `refresh.ts`

Automatic token refresh logic.

**Functions:**

- `refreshAccessToken()` - Manually refresh the access token
- `ensureValidToken()` - Check validity and refresh if needed
- `setupTokenRefresh(onRefreshed, onFailed)` - Auto-refresh setup (checks every minute, refreshes 5min before expiry)

### `protected.tsx`

Protected route components and HOCs.

**Components:**

- `<ProtectedRoute>` - Wrapper component that checks auth before rendering
- `withAuth(Component)` - HOC to protect any component

### `hooks.ts`

Custom React hooks for authentication.

**Hooks:**

- `useAuth()` - Get auth state, logout function, and token
- `useTokenRefresh()` - Set up automatic token refresh
- `useRequireAuth()` - Ensure auth with redirect

## 🚀 Usage Examples

### 1. Protect a Page with ProtectedRoute Component

```tsx
"use client";

import { ProtectedRoute } from "@/lib/auth";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div>
        <h1>Protected Dashboard</h1>
        <p>Only authenticated users can see this!</p>
      </div>
    </ProtectedRoute>
  );
}
```

### 2. Protect a Page with HOC

```tsx
"use client";

import { withAuth } from "@/lib/auth";

function DashboardPage() {
  return (
    <div>
      <h1>Protected Dashboard</h1>
      <p>Only authenticated users can see this!</p>
    </div>
  );
}

export default withAuth(DashboardPage);
```

### 3. Use Authentication Hook

```tsx
"use client";

import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const { isAuthenticated, isLoading, logout, token } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }

  return (
    <div>
      <h1>Profile</h1>
      <p>Token: {token?.substring(0, 20)}...</p>
      <Button onClick={logout}>Logout</Button>
    </div>
  );
}
```

### 4. Set Up Automatic Token Refresh (in Root Layout)

```tsx
"use client";

import { useTokenRefresh } from "@/lib/auth";

export default function RootLayout({ children }) {
  // This will automatically refresh tokens before they expire
  useTokenRefresh();

  return (
    <html>
      <body>{children}</body>
    </html>
  );
}
```

### 5. Manual Token Operations

```tsx
import {
  getAccessToken,
  isAuthenticated,
  clearAuthTokens,
  ensureValidToken,
} from "@/lib/auth";

// Check if user is logged in
if (isAuthenticated()) {
  console.log("User is logged in!");
}

// Get token for API calls
const token = getAccessToken();

// Ensure token is valid (refresh if needed)
const isValid = await ensureValidToken();

// Logout
clearAuthTokens();
```

### 6. Protected API Calls

```tsx
import { getAccessToken, ensureValidToken } from "@/lib/auth";

async function makeProtectedApiCall() {
  // Ensure token is valid
  await ensureValidToken();

  const token = getAccessToken();

  const response = await fetch("/api/protected", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return response.json();
}
```

## 🔄 Authentication Flow

### Login Flow

1. User clicks "Login with GitLab"
2. Redirected to GitLab OAuth
3. GitLab redirects back to `/login/success?session_id=xxx`
4. Frontend fetches tokens using session ID
5. Tokens stored in localStorage
6. User redirected to dashboard (or original destination)

### Protected Route Flow

1. User navigates to protected page
2. `ProtectedRoute` checks `isAuthenticated()`
3. If not authenticated → redirect to `/login?redirect=/current-path`
4. If authenticated → check token validity with `ensureValidToken()`
5. If token expired → automatically refresh using refresh token
6. If refresh fails → redirect to login
7. If valid → render protected content

### Auto-Refresh Flow

1. `useTokenRefresh()` sets up interval (checks every minute)
2. Before token expires (5min buffer), automatically calls refresh endpoint
3. New tokens stored in localStorage
4. If refresh fails → user redirected to login

## 🔐 Security Features

- **Token Expiry Tracking**: Stores expiry timestamp to prevent using expired tokens
- **Automatic Refresh**: Tokens refresh 5 minutes before expiry
- **Secure Storage**: Uses localStorage (consider httpOnly cookies for production)
- **Error Handling**: Automatic cleanup and redirect on auth failures
- **Race Condition Prevention**: Single refresh promise prevents multiple simultaneous refreshes

## 🛠️ Configuration

### Adjust Token Refresh Timing

In `refresh.ts`, modify the interval and buffer:

```typescript
// Check every 30 seconds instead of 60
const intervalId = setInterval(async () => {
  if (isTokenExpired(600)) {
    // Refresh 10 minutes before expiry
    await refreshAccessToken();
  }
}, 30000); // 30 seconds
```

### Custom Loading UI

```tsx
<ProtectedRoute
  fallback={
    <div className="custom-loader">
      <YourCustomSpinner />
      <p>Authenticating...</p>
    </div>
  }
>
  {/* Protected content */}
</ProtectedRoute>
```

## 📝 Best Practices

1. **Always use `ProtectedRoute`** for authenticated pages
2. **Set up `useTokenRefresh()`** in your root layout
3. **Use `ensureValidToken()`** before important API calls
4. **Clear tokens on logout** with `clearAuthTokens()`
5. **Check authentication** on the login page to avoid re-login

## 🐛 Troubleshooting

### User keeps getting logged out

- Check if token refresh endpoint is working
- Verify expiry time is set correctly
- Check browser console for errors

### Infinite redirect loop

- Ensure login page doesn't use `ProtectedRoute`
- Check that `isAuthenticated()` returns false after `clearAuthTokens()`

### Token not refreshing

- Verify `useTokenRefresh()` is called in a client component
- Check that refresh token is stored correctly
- Ensure refresh endpoint returns correct response format

## 📚 API Response Format

The authentication system expects the following response format from your API:

```typescript
{
  access_token: string;
  refresh_token: string;
  expires_in: number; // seconds until expiry
}
```

## 🎯 Next Steps

Consider implementing:

- **HTTP-only cookies** instead of localStorage for enhanced security
- **Refresh token rotation** for better security
- **Session management** with server-side validation
- **Remember me** functionality
- **Multi-tab synchronization** using BroadcastChannel API
