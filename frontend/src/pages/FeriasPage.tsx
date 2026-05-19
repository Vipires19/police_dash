import { Navigate } from "react-router-dom";

/** Redireciona rota legada /ferias para o módulo Afastamentos. */
export function FeriasPage() {
  return <Navigate to="/afastamentos" replace />;
}
