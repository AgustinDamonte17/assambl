import { ProyectoProvider } from "./estado/ProyectoContext";
import Shell from "./componentes/Shell";

export default function App() {
  return (
    <ProyectoProvider>
      <Shell />
    </ProyectoProvider>
  );
}
