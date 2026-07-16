import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/types";
import { useAuth } from "@/hooks/AuthContext";
import * as usersApi from "@/services/usersApi";

const ACT_AS_KEY = "actAsUserId";

interface ActAsContextValue {
  canUseGodMode: boolean;
  targetUser: User | null;
  targetUserId: number | null;
  efetivo: User[];
  setTargetUserId: (id: number | null) => void;
  clearTarget: () => void;
  /** Usuário efetivo das telas pessoais (target ou o próprio). */
  effectiveUser: User | null;
  isActingAs: boolean;
}

const ActAsContext = createContext<ActAsContextValue | undefined>(undefined);

function readStoredTargetId(): number | null {
  const raw = sessionStorage.getItem(ACT_AS_KEY);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? n : null;
}

export function ActAsProvider({ children }: { children: ReactNode }) {
  const { user, token, loading } = useAuth();
  const canUseGodMode = user?.role === "ADMIN";
  const [targetUserId, setTargetUserIdState] = useState<number | null>(() => readStoredTargetId());
  const [efetivo, setEfetivo] = useState<User[]>([]);

  useEffect(() => {
    if (loading) return;
    if (!canUseGodMode) {
      sessionStorage.removeItem(ACT_AS_KEY);
      setTargetUserIdState(null);
      setEfetivo([]);
      return;
    }
    if (!token) return;
    let cancelled = false;
    void usersApi.listEfetivo(token).then((list) => {
      if (cancelled) return;
      setEfetivo(list.filter((u) => u.status === "APPROVED" && u.is_active));
    });
    return () => {
      cancelled = true;
    };
  }, [loading, canUseGodMode, token]);

  useEffect(() => {
    if (loading || !canUseGodMode || targetUserId == null) return;
    if (efetivo.length === 0) return;
    if (!efetivo.some((u) => u.id === targetUserId)) {
      sessionStorage.removeItem(ACT_AS_KEY);
      setTargetUserIdState(null);
    }
  }, [loading, canUseGodMode, targetUserId, efetivo]);

  const setTargetUserId = useCallback(
    (id: number | null) => {
      if (!canUseGodMode) return;
      if (id == null) {
        sessionStorage.removeItem(ACT_AS_KEY);
        setTargetUserIdState(null);
        return;
      }
      sessionStorage.setItem(ACT_AS_KEY, String(id));
      setTargetUserIdState(id);
    },
    [canUseGodMode],
  );

  const clearTarget = useCallback(() => setTargetUserId(null), [setTargetUserId]);

  const targetUser = useMemo(
    () => (targetUserId != null ? efetivo.find((u) => u.id === targetUserId) ?? null : null),
    [efetivo, targetUserId],
  );

  const isActingAs = Boolean(canUseGodMode && targetUser && user && targetUser.id !== user.id);
  const effectiveUser = isActingAs ? targetUser : user;

  const value = useMemo(
    () => ({
      canUseGodMode,
      targetUser,
      targetUserId: isActingAs ? targetUserId : null,
      efetivo,
      setTargetUserId,
      clearTarget,
      effectiveUser,
      isActingAs,
    }),
    [
      canUseGodMode,
      targetUser,
      targetUserId,
      efetivo,
      setTargetUserId,
      clearTarget,
      effectiveUser,
      isActingAs,
    ],
  );

  return <ActAsContext.Provider value={value}>{children}</ActAsContext.Provider>;
}

export function useActAs(): ActAsContextValue {
  const ctx = useContext(ActAsContext);
  if (!ctx) {
    throw new Error("useActAs deve ser usado dentro de ActAsProvider");
  }
  return ctx;
}

/** Lê o target atual do sessionStorage (para apiFetch fora do React). */
export function getActAsUserIdFromStorage(): number | null {
  return readStoredTargetId();
}
