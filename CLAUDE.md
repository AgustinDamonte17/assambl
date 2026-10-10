# Convenciones del proyecto Assambl

- **Fundamentos de diseño sin citas.** Todo fundamento guardado en la «memoria» de Assambl (hoy los
  textos de Lumo en `software/backend/assambl/ia/` y las razones de la planta base en
  `software/backend/assambl/capas/planta_base.py`; el paquete de fundamentos se retiró y su documento quedó en
  `software/docs/archivo/` solo como consulta) es conocimiento propio de Assambl. No se citan libros, autores, normas, páginas
  ni nombres de personas: Assambl explica su razonamiento (principio, por qué, qué midió, qué se resigna) y la
  lógica que siguió. Vale para el código, la interfaz, la documentación y los fundamentos que se agreguen.
- Los fundamentos no son obligatorios: son exploración de alternativas fundamentada, no reglas como las de R03.
- **Interfaz de la app.** Antes de tocar pantallas, componentes o estilos de `software/frontend/`, seguí la skill
  `.claude/skills/assambl-ui/SKILL.md`: tipografía en tres roles (Chivo para títulos y todo lo que se lee,
  Chivo Mono solo para rótulos y datos) con su prueba rápida.
- **Lumo es el asistente fijo de Assambl.** No hay otros personajes. Su diseño (forma, paleta, estados y cuándo se
  usa cada uno) está en `software/lumo/lumo-final.html`; el componente es `software/frontend/src/componentes/lumo/`.
