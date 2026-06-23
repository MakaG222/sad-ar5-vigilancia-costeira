import { useCallback, useRef } from "react";

export function useToast() {
  const toastTimer = useRef(null);
  const setToastRef = useRef(null);

  const bind = useCallback((setToast) => {
    setToastRef.current = setToast;
  }, []);

  const showToast = useCallback((msg, severidade = "media") => {
    if (!setToastRef.current) return;
    setToastRef.current({ msg, severidade });
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToastRef.current?.(null), 5000);
  }, []);

  return { bind, showToast };
}
