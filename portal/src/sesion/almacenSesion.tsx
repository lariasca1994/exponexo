import React, { createContext, useContext, useState } from "react";
import { Navigate } from "react-router-dom";
import type { LoginStep1Response, TokenPairResponse, UserAccount, UserRole } from "../tipos/identidad";

interface MemorySessionState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserAccount | null;
  pendingMfa: (LoginStep1Response & { correo: string }) | null;
}

let memoryTokens: { accessToken: string | null; refreshToken: string | null } = {
  accessToken: null,
  refreshToken: null
};

export function getInMemoryTokens() {
  return memoryTokens;
}

export function setInMemoryTokens(accessToken: string | null, refreshToken: string | null) {
  memoryTokens = { accessToken, refreshToken };
}

interface SessionContextValue extends MemorySessionState {
  savePendingMfa: (correo: string, step1: LoginStep1Response) => void;
  establishSession: (tokens: TokenPairResponse) => void;
  clearSession: () => void;
}

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<MemorySessionState>({
    accessToken: null,
    refreshToken: null,
    user: null,
    pendingMfa: null
  });

  const savePendingMfa = (correo: string, step1: LoginStep1Response) => {
    setState((prev) => ({
      ...prev,
      pendingMfa: { ...step1, correo }
    }));
  };

  const establishSession = (tokens: TokenPairResponse) => {
    setInMemoryTokens(tokens.token_acceso, tokens.token_refresco);
    setState({
      accessToken: tokens.token_acceso,
      refreshToken: tokens.token_refresco,
      user: tokens.usuario,
      pendingMfa: null
    });
  };

  const clearSession = () => {
    setInMemoryTokens(null, null);
    setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      pendingMfa: null
    });
  };

  return (
    <SessionContext.Provider
      value={{
        ...state,
        savePendingMfa,
        establishSession,
        clearSession
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession debe usarse dentro de SessionProvider");
  }
  return ctx;
}

export function ProtectedRoute({
  allowedRoles,
  children
}: {
  allowedRoles?: UserRole[];
  children: React.ReactNode;
}) {
  const { user, accessToken } = useSession();
  if (!user || !accessToken) {
    return <Navigate to="/ingreso" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/inicio" replace />;
  }
  return <>{children}</>;
}
