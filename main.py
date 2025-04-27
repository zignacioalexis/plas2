import streamlit as st
import pandas as pd
import math
import json
import os
import sqlite3 # Importar sqlite3
from datetime import datetime

# --- Configuración de la Página ---
st.set_page_config(page_title="Calculadora de Producción v2", layout="wide")

# --- Nombre del Archivo de Base de Datos ---
DATABASE_FILE = "production_data.db"

# --- Funciones de Base de Datos ---

def init_db():
    """Inicializa la base de datos y crea la tabla 'machines' si no existe."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            # Usar TEXT para almacenar los diccionarios JSON
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS machines (
                    name TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    description TEXT,
                    setup_params TEXT NOT NULL,
                    production_params TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            ''')
            conn.commit()
        # st.toast("Base de datos inicializada correctamente.", icon="✅") # Opcional: feedback
    except sqlite3.Error as e:
        st.error(f"Error al inicializar la base de datos: {e}")

def get_all_machines_db():
    """Obtiene todas las configuraciones de máquinas desde la base de datos."""
    machines = {}
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.row_factory = sqlite3.Row # Devolver filas como diccionarios
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM machines ORDER BY name")
            rows = cursor.fetchall()
            for row in rows:
                machine_dict = dict(row)
                # Deserializar los parámetros JSON
                try:
                    machine_dict['setup_params'] = json.loads(machine_dict['setup_params'])
                    machine_dict['production_params'] = json.loads(machine_dict['production_params'])
                    machines[machine_dict['name']] = machine_dict
                except json.JSONDecodeError as json_err:
                     st.error(f"Error al decodificar JSON para la máquina {machine_dict.get('name', 'DESCONOCIDA')}: {json_err}")
                except Exception as e:
                     st.error(f"Error inesperado procesando máquina {machine_dict.get('name', 'DESCONOCIDA')}: {e}")

    except sqlite3.Error as e:
        st.error(f"Error al leer máquinas de la base de datos: {e}")
    return machines

def add_machine_db(config):
    """Agrega una nueva configuración de máquina a la base de datos."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO machines (name, type, description, setup_params, production_params, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                config['name'],
                config['type'],
                config.get('description', None),
                json.dumps(config['setup_params']), # Serializar a JSON
                json.dumps(config['production_params']), # Serializar a JSON
                config['created_at']
            ))
            conn.commit()
        st.success(f"✅ Máquina '{config['name']}' guardada en la base de datos.")
        return True
    except sqlite3.IntegrityError:
        st.error(f"⛔ Error: Ya existe una máquina con el nombre '{config['name']}'.")
        return False
    except sqlite3.Error as e:
        st.error(f"Error al guardar la máquina en la base de datos: {e}")
        return False

def update_machine_db(original_name, config):
    """Actualiza una configuración de máquina existente en la base de datos."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE machines
                SET name = ?, type = ?, description = ?, setup_params = ?, production_params = ?, updated_at = ?
                WHERE name = ?
            ''', (
                config['name'],
                config['type'],
                config.get('description', None),
                json.dumps(config['setup_params']), # Serializar a JSON
                json.dumps(config['production_params']), # Serializar a JSON
                config['updated_at'],
                original_name # Usar el nombre original en el WHERE
            ))
            conn.commit()
        st.success(f"✅ Máquina '{config['name']}' actualizada en la base de datos.")
        return True
    except sqlite3.Error as e:
        st.error(f"Error al actualizar la máquina en la base de datos: {e}")
        return False

def delete_machine_db(name):
    """Elimina una configuración de máquina de la base de datos."""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM machines WHERE name = ?", (name,))
            conn.commit()
        st.success(f"🗑️ Máquina '{name}' eliminada de la base de datos.")
        return True
    except sqlite3.Error as e:
        st.error(f"Error al eliminar la máquina de la base de datos: {e}")
        return False

# --- Inicializar Base de Datos al inicio ---
init_db()

# --- CSS (sin cambios) ---
st.markdown("""
<style>
/* Fondo y tipografía */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: #f4f6f9;
}
div.stApp {
    background: linear-gradient(to right, #ffffff, #e6e6e6);
}

/* Estilos para el título */
h1, h2, h3 {
    color: #333333;
    text-align: center;
}

/* Estilos para las tablas premium */
.custom-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1); /* Sombra sutil */
    border-radius: 5px; /* Bordes redondeados */
    overflow: hidden; /* Para que el borde redondeado aplique a th */
}
.custom-table th, .custom-table td {
    padding: 12px 15px;
    border: 1px solid #dddddd;
    text-align: center;
    font-size: 0.95em; /* Tamaño de fuente ligeramente menor */
}
.custom-table th {
    background-color: #4CAF50; /* Verde */
    color: white;
    font-weight: bold; /* Texto en negrita */
}
.custom-table tr:nth-child(even) {
    background-color: #f8f9fa; /* Gris muy claro para filas pares */
}
.custom-table tr:hover {
    background-color: #e9ecef; /* Gris claro al pasar el mouse */
}

/* Estilos para la barra de progreso de eficiencia */
.progress {
  background-color: #e9ecef; /* Fondo más suave */
  border-radius: 13px;
  padding: 3px;
  margin: 0;
  height: 26px; /* Un poco más alta */
}
.progress-bar {
  background: linear-gradient(to right, #4CAF50, #8BC34A); /* Gradiente verde */
  width: 0%;
  height: 20px;
  border-radius: 10px;
  text-align: center;
  color: white;
  line-height: 20px;
  font-weight: bold; /* Texto en negrita */
  transition: width 0.5s ease-in-out; /* Transición suave */
}

/* Estilos para tarjetas de máquinas */
.machine-card {
    padding: 20px; /* Más padding */
    margin: 15px 0; /* Más margen */
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    background-color: white;
    transition: transform 0.3s ease, box-shadow 0.3s ease; /* Transición suave */
    border-left: 5px solid #ccc; /* Borde por defecto */
}
.machine-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0,0,0,0.15); /* Sombra más pronunciada */
}
.machine-manual {
    border-left-color: #3498db; /* Azul */
}
.machine-semi {
    border-left-color: #f39c12; /* Naranja */
}
.machine-auto {
    border-left-color: #2ecc71; /* Verde esmeralda */
}
.machine-card h3 {
    margin-top: 0;
    margin-bottom: 10px;
    color: #333;
}
.machine-card p {
    font-size: 0.9em;
    color: #555;
    margin-bottom: 5px; /* Menos espacio entre párrafos */
}
.machine-card strong {
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# --- Constantes y estado inicial ---
MACHINE_TYPES = ["Manual", "Semi-Automática", "Automática"]

# Usar st.session_state solo para estado temporal de la UI, no para datos persistentes
if 'current_page' not in st.session_state:
    st.session_state.current_page = "calculator"
if 'editing_machine' not in st.session_state:
    st.session_state.editing_machine = None # Usar None para indicar que no se está editando

# --- Funciones de Renderizado (sin cambios significativos, solo formato) ---

def render_analysis_table(turno_minutos, tiempo_productivo, tiempo_perdido, eficiencia):
    """
    Construye una tabla HTML con el análisis de tiempos, mostrando la eficiencia como barra de progreso.
    """
    eficiencia_percent = float(eficiencia) if eficiencia else 0.0
    progress_bar_html = f'''
    <div class="progress">
      <div class="progress-bar" style="width: {eficiencia_percent:.2f}%; min-width: 50px;">
        {eficiencia_percent:.2f}%
      </div>
    </div>
    '''

    html = f'''
    <table class="custom-table">
      <thead>
        <tr>
          <th>Métrica</th>
          <th>Valor</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Tiempo Total Turno</td>
          <td>{turno_minutos:.2f} min</td>
        </tr>
        <tr>
          <td>Tiempo Productivo</td>
          <td>{tiempo_productivo:.2f} min</td>
        </tr>
        <tr>
          <td>Tiempo Perdido</td>
          <td>{tiempo_perdido:.2f} min</td>
        </tr>
        <tr>
          <td>Eficiencia</td>
          <td>{progress_bar_html}</td>
        </tr>
      </tbody>
    </table>
    '''
    return html


def render_interruptions_table(interrupciones_dict, turno_minutos):
    """
    Construye una tabla HTML para el detalle de interrupciones, mostrando además el porcentaje que representa sobre el turno.
    """
    rows = ""
    total_interrupcion_min = 0
    for tipo, tiempo in interrupciones_dict.items():
        tiempo_float = float(tiempo) # Asegurar que es float
        if tiempo_float > 0:  # Solo mostrar interrupciones con tiempo > 0
            porcentaje = (tiempo_float / turno_minutos) * 100 if turno_minutos > 0 else 0
            rows += f"<tr><td>{tipo}</td><td>{tiempo_float:.2f} min</td><td>{porcentaje:.2f}%</td></tr>"
            total_interrupcion_min += tiempo_float

    # Fila de Total
    total_porcentaje = (total_interrupcion_min / turno_minutos) * 100 if turno_minutos > 0 else 0
    rows += f"<tr style='font-weight: bold; background-color: #e9ecef;'><td>Total Interrupciones</td><td>{total_interrupcion_min:.2f} min</td><td>{total_porcentaje:.2f}%</td></tr>"


    html = f'''
    <table class="custom-table">
      <thead>
        <tr>
          <th>Tipo</th>
          <th>Tiempo (min)</th>
          <th>% Turno</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    '''
    return html

# --- Páginas de la Aplicación ---

def machine_configuration_page():
    """Página para gestionar configuraciones de máquinas usando la BD."""
    st.title("⚙️ Configuración de Máquinas")

    # Sección para agregar nueva máquina
    with st.expander("➕ Agregar Nueva Máquina", expanded=False):
        # ... (Formulario de agregar máquina - igual que antes) ...
        col1, col2 = st.columns(2)
        with col1:
            new_machine_name = st.text_input("Nombre de la Máquina", key="new_machine_name")
            new_machine_type = st.selectbox("Tipo de Máquina", options=MACHINE_TYPES, key="new_machine_type")

        with col2:
            new_machine_description = st.text_area("Descripción", key="new_machine_description",
                                               placeholder="Breve descripción de la máquina...")

        st.subheader("Parámetros de Setup")
        setup_col1, setup_col2 = st.columns(2)

        # Parámetros de setup según el tipo de máquina
        new_setup_params = {}

        with setup_col1:
             # Parámetros comunes a todos los tipos
            new_setup_params["calibracion"] = st.number_input("Tiempo de Calibración (min)",
                                                          min_value=0, value=10, step=1, key="new_calibracion")
            new_setup_params["otros"] = st.number_input("Tiempo de Otros (min)",
                                                    min_value=0, value=30, step=1, key="new_otros")
            new_setup_params["cambio_rollo"] = st.number_input("Tiempo de Cambio de Rollo (min)",
                                                           min_value=0, value=4, step=1, key="new_cambio_rollo")
            new_setup_params["cambio_producto"] = st.number_input("Tiempo de Cambio de Producto (min)",
                                                              min_value=0, value=15, step=1, key="new_cambio_producto")

        with setup_col2:
             # Parámetros específicos para Manual y Semi-Automática
            if new_machine_type in ["Manual", "Semi-Automática"]:
                new_setup_params["cambio_cuchillo"] = st.number_input("Tiempo de Cambio de Cuchillo (min)",
                                                                  min_value=0, value=30, step=1,
                                                                  key="new_cambio_cuchillo")
                new_setup_params["cambio_perforador"] = st.number_input("Tiempo de Cambio de Perforador (min)",
                                                                    min_value=0, value=10, step=1,
                                                                    key="new_cambio_perforador")
                new_setup_params["cambio_paquete"] = st.number_input("Tiempo de Cambio de Paquete (min)",
                                                                 min_value=0, value=5, step=1, key="new_cambio_paquete")

             # Parámetro específico para Manual
            if new_machine_type == "Manual":
                new_setup_params["empaque"] = st.number_input("Tiempo de Empaque (segundos)",
                                                          min_value=0, value=60, step=5, key="new_empaque")


        st.subheader("Parámetros de Producción")
        prod_col1, prod_col2 = st.columns(2)

        # Parámetros de producción
        new_production_params = {}

        with prod_col1:
            new_production_params["unidades_por_minuto"] = st.number_input("Unidades por Minuto",
                                                                       min_value=1, value=48, step=1, key="new_upm")
            new_production_params["peso_por_unidad"] = st.number_input("Peso por Unidad (gramos)",
                                                                   min_value=0.01, value=45.3, step=0.1, key="new_peso")

        with prod_col2:
             # Para máquinas Manual y Semi-Automática necesitamos el ratio productivo
            if new_machine_type in ["Manual", "Semi-Automática"]:
                st.write("Tiempo de Ciclo Productivo:")
                cycle_seconds = st.number_input("Duración del Ciclo (segundos)",
                                                min_value=1, value=32, step=1, key="new_cycle_time")
                productive_seconds = st.number_input("Tiempo Productivo del Ciclo (segundos)",
                                                     min_value=1, value=27, step=1,
                                                     key="new_productive_time")
                # Validar que productivo <= ciclo
                if productive_seconds > cycle_seconds:
                    st.warning("El tiempo productivo no puede ser mayor al tiempo total del ciclo. Ajustando...")
                    productive_seconds = cycle_seconds

                new_production_params["ciclo_total"] = cycle_seconds
                new_production_params["ciclo_productivo"] = productive_seconds
                new_production_params["ratio_productivo"] = productive_seconds / cycle_seconds if cycle_seconds > 0 else 0
            else:
                 # Para máquinas Automáticas, el ratio es siempre 1
                new_production_params["ratio_productivo"] = 1.0
                # Opcional: guardar ciclo y tiempo productivo como N/A o 0 si se prefiere
                new_production_params["ciclo_total"] = 0
                new_production_params["ciclo_productivo"] = 0


        # Botón para guardar la configuración en la BD
        if st.button("💾 Guardar Configuración", key="save_new_machine", type="primary"):
            if not new_machine_name:
                st.error("⛔ Error: El nombre de la máquina es obligatorio.")
            else:
                # Crear la configuración de la máquina
                machine_config_to_add = {
                    "name": new_machine_name.strip(), # Limpiar espacios
                    "type": new_machine_type,
                    "description": new_machine_description.strip(),
                    "setup_params": new_setup_params,
                    "production_params": new_production_params,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Guardar en la base de datos
                if add_machine_db(machine_config_to_add):
                    # Limpiar formulario (opcional, reseteando keys o cambiando de página)
                    # st.session_state.new_machine_name = "" # etc... o simplemente rerun
                    st.rerun() # Recargar para mostrar la nueva máquina

    # --- Lista de máquinas configuradas (leídas desde la BD) ---
    st.divider()
    st.header("📋 Máquinas Configuradas")
    all_machines = get_all_machines_db() # Leer desde la BD cada vez que se renderiza la página

    if not all_machines:
        st.info("ℹ️ No hay máquinas configuradas. Agrega una nueva máquina usando el formulario de arriba.")
    else:
        # Mostrar las máquinas en una cuadrícula
        num_columns = 3 # Ajusta según preferencia
        machine_cols = st.columns(num_columns)
        machine_list = list(all_machines.items()) # Convertir a lista para indexar

        for i, (name, config) in enumerate(machine_list):
            col_idx = i % num_columns

            # Determinar la clase CSS según el tipo de máquina
            machine_class = "machine-card" # Clase base
            if config["type"] == "Manual":
                machine_class += " machine-manual"
            elif config["type"] == "Semi-Automática":
                machine_class += " machine-semi"
            else: # Automática
                machine_class += " machine-auto"

            with machine_cols[col_idx]:
                # Crear tarjeta de máquina
                # Usar .get para acceder a claves opcionales como 'updated_at'
                updated_info = f"<p><small><i>Actualizada: {config['updated_at']}</i></small></p>" if config.get('updated_at') else ""
                st.markdown(f"""
                <div class="{machine_class}">
                    <h3>{name}</h3>
                    <p><strong>Tipo:</strong> {config["type"]}</p>
                    <p><strong>Descripción:</strong> {config.get("description") or "N/A"}</p>
                    <p><small>Creada: {config["created_at"]}</small></p>
                    {updated_info}
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción (usar columnas dentro de la columna de la cuadrícula)
                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button("🗑️ Eliminar", key=f"delete_{name}", help=f"Eliminar {name}"):
                        # Podrías añadir una confirmación aquí si quieres
                        if delete_machine_db(name):
                            st.rerun() # Recargar para quitar la máquina eliminada

                with action_cols[1]:
                    if st.button("✏️ Editar", key=f"edit_{name}", help=f"Editar {name}"):
                        st.session_state.editing_machine = name # Guardar nombre de máquina a editar
                        st.rerun() # Recargar para mostrar el formulario de edición

    # --- Formulario de edición de máquina ---
    if st.session_state.editing_machine:
        machine_to_edit_name = st.session_state.editing_machine
        # Obtener la configuración más reciente de la BD para editar
        all_machines_for_edit = get_all_machines_db()
        if machine_to_edit_name not in all_machines_for_edit:
            st.error(f"Error: No se encontró la máquina '{machine_to_edit_name}' para editar. Puede haber sido eliminada.")
            st.session_state.editing_machine = None # Limpiar estado
            st.rerun()
        else:
            machine_config = all_machines_for_edit[machine_to_edit_name]

            st.divider()
            st.header(f"✏️ Editando Máquina: {machine_to_edit_name}")

            # --- Formulario de Edición (similar al de agregar, pero con valores prellenados) ---
            col1, col2 = st.columns(2)
            with col1:
                edit_name = st.text_input("Nombre de la Máquina", value=machine_config["name"], key="edit_machine_name")
                # Encuentra el índice correcto para el selectbox
                try:
                    type_index = MACHINE_TYPES.index(machine_config["type"])
                except ValueError:
                    type_index = 0 # Default al primero si hay inconsistencia
                edit_type = st.selectbox("Tipo de Máquina", options=MACHINE_TYPES,
                                             index=type_index, key="edit_machine_type")

            with col2:
                edit_description = st.text_area("Descripción", value=machine_config.get("description", ""),
                                                    key="edit_machine_description")

            st.subheader("Parámetros de Setup")
            setup_col1, setup_col2 = st.columns(2)

            # Editar parámetros de setup
            edit_setup_params = {}
            setup_config = machine_config["setup_params"] # Ya es un dict

            with setup_col1:
                # Parámetros comunes a todos los tipos
                edit_setup_params["calibracion"] = st.number_input("Tiempo de Calibración (min)",
                                                              min_value=0, value=setup_config.get("calibracion", 10),
                                                              step=1, key="edit_calibracion")
                edit_setup_params["otros"] = st.number_input("Tiempo de Otros (min)",
                                                        min_value=0, value=setup_config.get("otros", 30),
                                                        step=1, key="edit_otros")
                edit_setup_params["cambio_rollo"] = st.number_input("Tiempo de Cambio de Rollo (min)",
                                                               min_value=0, value=setup_config.get("cambio_rollo", 4),
                                                               step=1, key="edit_cambio_rollo")
                edit_setup_params["cambio_producto"] = st.number_input("Tiempo de Cambio de Producto (min)",
                                                                  min_value=0,
                                                                  value=setup_config.get("cambio_producto", 15),
                                                                  step=1, key="edit_cambio_producto")

            with setup_col2:
                # Parámetros específicos para Manual y Semi-Automática
                if edit_type in ["Manual", "Semi-Automática"]:
                    edit_setup_params["cambio_cuchillo"] = st.number_input("Tiempo de Cambio de Cuchillo (min)",
                                                                      min_value=0,
                                                                      value=setup_config.get("cambio_cuchillo", 30),
                                                                      step=1, key="edit_cambio_cuchillo")
                    edit_setup_params["cambio_perforador"] = st.number_input("Tiempo de Cambio de Perforador (min)",
                                                                        min_value=0,
                                                                        value=setup_config.get("cambio_perforador", 10),
                                                                        step=1, key="edit_cambio_perforador")
                    edit_setup_params["cambio_paquete"] = st.number_input("Tiempo de Cambio de Paquete (min)",
                                                                     min_value=0,
                                                                     value=setup_config.get("cambio_paquete", 5),
                                                                     step=1, key="edit_cambio_paquete")
                # Limpiar claves si el tipo de máquina cambia a uno donde no aplican
                else:
                    edit_setup_params.pop("cambio_cuchillo", None)
                    edit_setup_params.pop("cambio_perforador", None)
                    edit_setup_params.pop("cambio_paquete", None)
                    edit_setup_params.pop("empaque", None) # También limpiar empaque si no es manual


                # Parámetro específico para Manual
                if edit_type == "Manual":
                    edit_setup_params["empaque"] = st.number_input("Tiempo de Empaque (segundos)",
                                                              min_value=0, value=setup_config.get("empaque", 60),
                                                              step=5, key="edit_empaque")
                elif "empaque" in edit_setup_params: # Limpiar si se cambia de Manual a otro tipo
                     edit_setup_params.pop("empaque", None)


            st.subheader("Parámetros de Producción")
            prod_col1, prod_col2 = st.columns(2)

            # Editar parámetros de producción
            edit_production_params = {}
            prod_config = machine_config["production_params"] # Ya es un dict

            with prod_col1:
                edit_production_params["unidades_por_minuto"] = st.number_input("Unidades por Minuto",
                                                                           min_value=1,
                                                                           value=prod_config.get("unidades_por_minuto", 48),
                                                                           step=1, key="edit_upm")
                edit_production_params["peso_por_unidad"] = st.number_input("Peso por Unidad (gramos)",
                                                                       min_value=0.01,
                                                                       value=prod_config.get("peso_por_unidad", 45.3),
                                                                       step=0.1, key="edit_peso")

            with prod_col2:
                # Para máquinas Manual y Semi-Automática necesitamos el ratio productivo
                if edit_type in ["Manual", "Semi-Automática"]:
                    st.write("Tiempo de Ciclo Productivo:")
                    edit_cycle_seconds = st.number_input("Duración del Ciclo (segundos)",
                                                    min_value=1, value=prod_config.get("ciclo_total", 32),
                                                    step=1, key="edit_cycle_time")
                    edit_productive_seconds = st.number_input("Tiempo Productivo del Ciclo (segundos)",
                                                         min_value=1,
                                                         value=prod_config.get("ciclo_productivo", 27),
                                                         step=1, key="edit_productive_time")

                    # Validar que productivo <= ciclo
                    if edit_productive_seconds > edit_cycle_seconds:
                        st.warning("El tiempo productivo no puede ser mayor al tiempo total del ciclo. Ajustando...")
                        edit_productive_seconds = edit_cycle_seconds

                    edit_production_params["ciclo_total"] = edit_cycle_seconds
                    edit_production_params["ciclo_productivo"] = edit_productive_seconds
                    edit_production_params["ratio_productivo"] = edit_productive_seconds / edit_cycle_seconds if edit_cycle_seconds > 0 else 0
                else:
                    # Para máquinas Automáticas, el ratio es siempre 1
                    edit_production_params["ratio_productivo"] = 1.0
                    # Limpiar/resetear valores de ciclo si se cambia a Automática
                    edit_production_params["ciclo_total"] = 0
                    edit_production_params["ciclo_productivo"] = 0

            # Botones para guardar o cancelar edición
            edit_action_cols = st.columns(2)
            with edit_action_cols[0]:
                if st.button("✅ Guardar Cambios", key="save_edit_machine", type="primary"):
                    new_name = edit_name.strip()
                    if not new_name:
                        st.error("⛔ Error: El nombre de la máquina es obligatorio.")
                    else:
                        # Crear la configuración actualizada
                        updated_config = {
                            "name": new_name,
                            "type": edit_type,
                            "description": edit_description.strip(),
                            "setup_params": edit_setup_params,
                            "production_params": edit_production_params,
                            # Mantener created_at original, añadir/actualizar updated_at
                            "created_at": machine_config.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        # Actualizar en la base de datos usando el nombre original como clave
                        if update_machine_db(machine_to_edit_name, updated_config):
                            st.session_state.editing_machine = None # Terminar edición
                            st.rerun() # Recargar para mostrar cambios

            with edit_action_cols[1]:
                if st.button("❌ Cancelar", key="cancel_edit_machine"):
                    st.session_state.editing_machine = None # Terminar edición
                    st.rerun() # Recargar para ocultar formulario


def production_calculator_page():
    """Página para calcular la producción usando máquinas configuradas desde la BD."""
    st.title("🏭 Calculadora de Producción")

    # Obtener máquinas de la BD para el selector
    available_machines = get_all_machines_db()

    if not available_machines:
        st.warning("⚠️ No hay máquinas configuradas en la base de datos.")
        if st.button("Ir a Configuración de Máquinas"):
            st.session_state.current_page = "configuration"
            st.rerun()
        return # Detener ejecución si no hay máquinas

    # Seleccionar máquina
    machine_names = list(available_machines.keys())
    # Mantener la máquina seleccionada si ya existe una en session_state, si no, default a la primera
    selected_machine_name = st.session_state.get('selected_machine_calculator', machine_names[0])
    if selected_machine_name not in machine_names: # Si la máquina guardada ya no existe
         selected_machine_name = machine_names[0]

    selected_machine = st.selectbox(
        "Seleccione una Máquina",
        options=machine_names,
        index=machine_names.index(selected_machine_name), # Establecer índice basado en nombre
        key='selected_machine_calculator' # Guardar selección en session_state
        )
    machine_config = available_machines[selected_machine] # Obtener config de la máquina seleccionada

    # Mostrar información de la máquina seleccionada
    st.header(f"📊 Calculando para: {selected_machine} ({machine_config['type']})")
    if machine_config.get("description"):
        st.info(f"Descripción: {machine_config['description']}")

    # --- Parámetros de operación (igual que antes) ---
    with st.expander("🔧 Configuración Operativa", expanded=True):
         col1, col2 = st.columns(2)
         with col1:
             turno_horas = st.number_input(
                 "Duración del Turno (horas)",
                 min_value=1.0, max_value=24.0, value=8.0, step=0.5, key="turno_horas"
             )
             desayuno = st.checkbox("Incluir desayuno (15 min)", key="desayuno", value=True) # Default True
             almuerzo = st.checkbox("Incluir almuerzo (60 min)", key="almuerzo", value=True) # Default True

         with col2:
             st.subheader("Interrupciones Variables (Eventos)")
             # Variables de interrupciones según el tipo de máquina
             interrupciones = {} # Diccionario para almacenar las cantidades de cada evento

             # Cambios de rollo y producto son comunes a todos los tipos
             interrupciones["cambios_rollo"] = st.number_input(
                 "Nº Cambios de rollo", min_value=0, max_value=100, value=2, step=1, key="n_cambios_rollo"
             )
             interrupciones["cambios_producto"] = st.number_input(
                 "Nº Cambios de producto", min_value=0, max_value=100, value=1, step=1, key="n_cambios_producto"
             )

             # Cambios específicos según el tipo de máquina
             if machine_config["type"] in ["Manual", "Semi-Automática"]:
                 interrupciones["cambios_cuchillo"] = st.number_input(
                     "Nº Cambios de cuchillo", min_value=0, max_value=100, value=0, step=1, key="n_cambios_cuchillo"
                 )
                 interrupciones["cambios_perforador"] = st.number_input(
                     "Nº Cambios de perforador", min_value=0, max_value=100, value=0, step=1, key="n_cambios_perforador"
                 )
                 interrupciones["cambios_paquete"] = st.number_input(
                     "Nº Cambios de paquete", min_value=0, max_value=100, value=0, step=1, key="n_cambios_paquete"
                 )

             if machine_config["type"] == "Manual":
                 # Nota: El cálculo usa el tiempo de empaque en *minutos*, pero el input es por evento.
                 # El tiempo por evento está en setup_params["empaque"] (segundos).
                 interrupciones["cambios_empaque"] = st.number_input(
                     "Nº Cambios de empaque", min_value=0, max_value=100, value=0, step=1, key="n_cambios_empaque"
                 )

    # --- Cálculos ---
    try:
        # Obtener parámetros de la máquina (ya son diccionarios)
        setup_params = machine_config["setup_params"]
        production_params = machine_config["production_params"]

        # Cálculo de tiempos
        turno_minutos = turno_horas * 60

        # Interrupciones fijas (Base + Comidas)
        # Usar .get() con default por si alguna clave no existe en alguna configuración vieja
        interrupciones_fijas = setup_params.get("calibracion", 0) + setup_params.get("otros", 0)
        tiempo_comidas = (15 if desayuno else 0) + (60 if almuerzo else 0)

        # Interrupciones variables (Eventos * Tiempo por evento)
        interrupciones_variables = 0
        detalle_interrupciones_variables = {} # Para la tabla de desglose

        # Iterar sobre los eventos ingresados por el usuario
        for key, n_eventos in interrupciones.items():
            tiempo_por_evento = 0
            nombre_evento = ""
            if n_eventos > 0:
                if key == "cambios_rollo":
                    tiempo_por_evento = setup_params.get("cambio_rollo", 0)
                    nombre_evento = "Cambios Rollo"
                elif key == "cambios_producto":
                    tiempo_por_evento = setup_params.get("cambio_producto", 0)
                    nombre_evento = "Cambios Producto"
                elif key == "cambios_cuchillo":
                    tiempo_por_evento = setup_params.get("cambio_cuchillo", 0)
                    nombre_evento = "Cambios Cuchillo"
                elif key == "cambios_perforador":
                    tiempo_por_evento = setup_params.get("cambio_perforador", 0)
                    nombre_evento = "Cambios Perforador"
                elif key == "cambios_paquete":
                    tiempo_por_evento = setup_params.get("cambio_paquete", 0)
                    nombre_evento = "Cambios Paquete"
                elif key == "cambios_empaque":
                    tiempo_empaque_seg = setup_params.get("empaque", 0)
                    tiempo_por_evento = tiempo_empaque_seg / 60.0 # Convertir a minutos
                    nombre_evento = "Cambios Empaque"

                tiempo_total_evento = n_eventos * tiempo_por_evento
                if tiempo_total_evento > 0 and nombre_evento:
                    interrupciones_variables += tiempo_total_evento
                    detalle_interrupciones_variables[f"{nombre_evento} ({n_eventos}x)"] = tiempo_total_evento


        tiempo_neto_disponible = turno_minutos - (interrupciones_fijas + tiempo_comidas + interrupciones_variables)

        if tiempo_neto_disponible <= 0:
            st.error(f"⛔ Error: El tiempo total de interrupciones ({interrupciones_fijas + tiempo_comidas + interrupciones_variables:.1f} min) "
                     f"excede o iguala la duración del turno ({turno_minutos:.1f} min). No hay tiempo para producir.")
            # Mostrar desglose de tiempos aunque haya error
            st.subheader("⏳ Desglose de Tiempos (Estimado)")
            tiempo_perdido_total = interrupciones_fijas + tiempo_comidas + interrupciones_variables
            eficiencia = 0
            analysis_html = render_analysis_table(turno_minutos, 0, tiempo_perdido_total, eficiencia)
            with st.expander("Ver Análisis de Tiempos", expanded=True):
                st.markdown(analysis_html, unsafe_allow_html=True)

            # Detalle interrupciones
            interrupciones_dict_error = {
                 "Calibración Fija": setup_params.get("calibracion", 0),
                 "Otros Fijos": setup_params.get("otros", 0),
                 "Comidas": tiempo_comidas,
                 **detalle_interrupciones_variables # Unir diccionarios
            }
            with st.expander("🔍 Detalle de Interrupciones", expanded=False):
                 interruptions_html = render_interruptions_table(interrupciones_dict_error, turno_minutos)
                 st.markdown(interruptions_html, unsafe_allow_html=True)
            return # Detener cálculo

        # Ajuste por ratio productivo (si aplica)
        ratio_productivo = production_params.get("ratio_productivo", 1.0)
        tiempo_efectivo_produccion = tiempo_neto_disponible * ratio_productivo
        tiempo_detenido_ciclos = tiempo_neto_disponible * (1 - ratio_productivo) # Tiempo perdido *dentro* del ciclo operativo

        # Cálculo de producción
        unidades_por_minuto = production_params.get("unidades_por_minuto", 0)
        peso_por_unidad_g = production_params.get("peso_por_unidad", 0)

        unidades_estimadas = unidades_por_minuto * tiempo_efectivo_produccion
        peso_total_kg = unidades_estimadas * peso_por_unidad_g / 1000 if peso_por_unidad_g > 0 else 0

        # Cálculo de eficiencia OEE (simplificado como Disponibilidad * Rendimiento)
        # Disponibilidad = tiempo_neto_disponible / turno_minutos
        # Rendimiento = ratio_productivo (asumiendo velocidad estándar es la configurada)
        # Calidad = 100% (no se mide aquí)
        eficiencia_oee = (tiempo_efectivo_produccion / turno_minutos) * 100 if turno_minutos > 0 else 0

        # --- Resultados ---
        st.success("📈 Resultados de Producción Estimados")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            # Añadir rango simple (ej. +/- 5%)
            delta_unidades = unidades_estimadas * 0.05
            st.metric("Unidades Estimadas", f"{unidades_estimadas:,.0f}",
                      delta=f"± {delta_unidades:,.0f} uds", delta_color="off",
                      help=f"Rango aprox: {unidades_estimadas - delta_unidades:,.0f} - {unidades_estimadas + delta_unidades:,.0f}")
        with res_col2:
            delta_peso = peso_total_kg * 0.05
            st.metric("Peso Total Estimado", f"{peso_total_kg:,.1f} kg",
                      delta=f"± {delta_peso:,.1f} kg", delta_color="off",
                      help=f"Rango aprox: {peso_total_kg - delta_peso:,.1f} - {peso_total_kg + delta_peso:,.1f} kg")

        # Análisis de tiempos
        st.subheader("⏳ Análisis de Tiempos y Eficiencia")
        tiempo_perdido_total = turno_minutos - tiempo_efectivo_produccion
        analysis_html = render_analysis_table(turno_minutos, tiempo_efectivo_produccion, tiempo_perdido_total, eficiencia_oee)
        with st.expander("Ver Análisis de Tiempos", expanded=True):
            st.markdown(analysis_html, unsafe_allow_html=True)

        # Detalle de interrupciones
        interrupciones_dict = {
            "Calibración Fija": setup_params.get("calibracion", 0),
            "Otros Fijos": setup_params.get("otros", 0),
            "Comidas": tiempo_comidas,
             **detalle_interrupciones_variables # Unir diccionarios
        }
        # Añadir tiempo de paradas por ciclo si aplica
        if machine_config["type"] in ["Manual", "Semi-Automática"] and tiempo_detenido_ciclos > 0:
            interrupciones_dict["Paradas por Ciclo"] = tiempo_detenido_ciclos

        with st.expander("🔍 Detalle de Interrupciones", expanded=False):
            interruptions_html = render_interruptions_table(interrupciones_dict, turno_minutos)
            st.markdown(interruptions_html, unsafe_allow_html=True)

    except KeyError as e:
        st.error(f"⛔ Error de Configuración: Falta el parámetro '{e}' en la configuración de la máquina '{selected_machine}'. Por favor, edite la máquina y asegúrese de que todos los campos necesarios estén completos.")
    except Exception as e:
        st.error(f"⛔ Ocurrió un error inesperado durante el cálculo: {e}")
        st.exception(e) # Muestra el traceback completo para depuración


# --- Función Principal y Navegación ---
def main():
    """Función principal de la aplicación con navegación en sidebar."""
    with st.sidebar:
        st.title("📊 Menú Principal")
        st.markdown("---")

        # Botones de Navegación
        page_selection = st.radio(
            "Seleccione una página:",
            ("🧮 Calculadora", "⚙️ Configurar Máquinas"),
            key="page_selector",
            # Establecer el índice inicial basado en st.session_state.current_page
            index=0 if st.session_state.get('current_page', 'calculator') == 'calculator' else 1
        )

        # Actualizar la página actual en session_state basado en la selección del radio
        if page_selection == "🧮 Calculadora":
            st.session_state.current_page = "calculator"
        else:
            st.session_state.current_page = "configuration"

        st.markdown("---")
        st.info(f"Base de datos: `{DATABASE_FILE}`")
        st.caption(f"Fecha actual: {datetime.now().strftime('%Y-%m-%d')}")


    # Mostrar la página correspondiente según el estado
    if st.session_state.current_page == "calculator":
        production_calculator_page()
    elif st.session_state.current_page == "configuration":
        machine_configuration_page()
    else: # Fallback por si acaso
         st.session_state.current_page = "calculator"
         production_calculator_page()


if __name__ == "__main__":
    main()