import streamlit as st
import pandas as pd
import math
import json
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calculadora de Producción Configurable", layout="wide")

# CSS Premium para la aplicación
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
}
.custom-table th, .custom-table td {
    padding: 12px 15px;
    border: 1px solid #dddddd;
    text-align: center;
}
.custom-table th {
    background-color: #4CAF50;
    color: white;
}
.custom-table tr:nth-child(even) {
    background-color: #f3f3f3;
}
.custom-table tr:hover {
    background-color: #f1f1f1;
}

/* Estilos para la barra de progreso de eficiencia */
.progress {
  background-color: #e0e0e0;
  border-radius: 13px;
  padding: 3px;
  margin: 0;
}
.progress-bar {
  background-color: #4CAF50;
  width: 0%;
  height: 20px;
  border-radius: 10px;
  text-align: center;
  color: white;
  line-height: 20px;
}

/* Estilos para tarjetas de máquinas */
.machine-card {
    padding: 15px;
    margin: 10px 0;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    background-color: white;
    transition: transform 0.3s;
}
.machine-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}
.machine-manual {
    border-left: 5px solid #3498db;
}
.machine-semi {
    border-left: 5px solid #f39c12;
}
.machine-auto {
    border-left: 5px solid #2ecc71;
}
</style>
""", unsafe_allow_html=True)

# Constantes y configuración inicial
MACHINE_TYPES = ["Manual", "Semi-Automática", "Automática"]
CONFIG_FILE = "machine_config.json"

# Inicializar session_state para almacenar configuraciones
if 'machines' not in st.session_state:
    # Intentar cargar configuraciones desde archivo
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                st.session_state.machines = json.load(f)
        except:
            st.session_state.machines = {}
    else:
        st.session_state.machines = {}

if 'current_page' not in st.session_state:
    st.session_state.current_page = "calculator"


def save_configurations():
    """Guarda las configuraciones de máquinas en un archivo JSON"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(st.session_state.machines, f, indent=4)


def render_analysis_table(turno_minutos, tiempo_productivo, tiempo_perdido, eficiencia):
    """
    Construye una tabla HTML con el análisis de tiempos, mostrando la eficiencia como barra de progreso.
    """
    eficiencia_percent = float(eficiencia)
    progress_bar_html = f'''
    <div class="progress">
      <div class="progress-bar" style="width: {eficiencia_percent}%; min-width: 50px;">
        {eficiencia_percent:.2f}%
      </div>
    </div>
    '''

    html = f'''
    <table class="custom-table">
      <tr>
        <th>Métrica</th>
        <th>Valor</th>
      </tr>
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
    </table>
    '''
    return html


def render_interruptions_table(interrupciones_dict, turno_minutos):
    """
    Construye una tabla HTML para el detalle de interrupciones, mostrando además el porcentaje que representa sobre el turno.
    """
    rows = ""
    for tipo, tiempo in interrupciones_dict.items():
        if tiempo > 0:  # Solo mostrar interrupciones con tiempo > 0
            porcentaje = (tiempo / turno_minutos) * 100 if turno_minutos > 0 else 0
            rows += f"<tr><td>{tipo}</td><td>{tiempo:.2f} min</td><td>{porcentaje:.2f}%</td></tr>"

    html = f'''
    <table class="custom-table">
      <tr>
        <th>Tipo</th>
        <th>Tiempo (min)</th>
        <th>% Turno</th>
      </tr>
      {rows}
    </table>
    '''
    return html


def machine_configuration_page():
    """Página para gestionar configuraciones de máquinas"""
    st.title("⚙️ Configuración de Máquinas")

    # Sección para agregar nueva máquina
    with st.expander("➕ Agregar Nueva Máquina", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            machine_name = st.text_input("Nombre de la Máquina", key="new_machine_name")
            machine_type = st.selectbox("Tipo de Máquina", options=MACHINE_TYPES, key="new_machine_type")

        with col2:
            machine_description = st.text_area("Descripción", key="new_machine_description",
                                               placeholder="Breve descripción de la máquina...")

        st.subheader("Parámetros de Setup")
        setup_col1, setup_col2 = st.columns(2)

        # Parámetros de setup según el tipo de máquina
        setup_params = {}

        with setup_col1:
            # Parámetros comunes a todos los tipos
            setup_params["calibracion"] = st.number_input("Tiempo de Calibración (min)",
                                                          min_value=0, value=10, step=1, key="new_calibracion")
            setup_params["otros"] = st.number_input("Tiempo de Otros (min)",
                                                    min_value=0, value=30, step=1, key="new_otros")
            setup_params["cambio_rollo"] = st.number_input("Tiempo de Cambio de Rollo (min)",
                                                           min_value=0, value=4, step=1, key="new_cambio_rollo")
            setup_params["cambio_producto"] = st.number_input("Tiempo de Cambio de Producto (min)",
                                                              min_value=0, value=15, step=1, key="new_cambio_producto")

        with setup_col2:
            # Parámetros específicos para Manual y Semi-Automática
            if machine_type in ["Manual", "Semi-Automática"]:
                setup_params["cambio_cuchillo"] = st.number_input("Tiempo de Cambio de Cuchillo (min)",
                                                                  min_value=0, value=30, step=1,
                                                                  key="new_cambio_cuchillo")
                setup_params["cambio_perforador"] = st.number_input("Tiempo de Cambio de Perforador (min)",
                                                                    min_value=0, value=10, step=1,
                                                                    key="new_cambio_perforador")
                setup_params["cambio_paquete"] = st.number_input("Tiempo de Cambio de Paquete (min)",
                                                                 min_value=0, value=5, step=1, key="new_cambio_paquete")

            # Parámetro específico para Manual
            if machine_type == "Manual":
                setup_params["empaque"] = st.number_input("Tiempo de Empaque (segundos)",
                                                          min_value=0, value=60, step=5, key="new_empaque")

        st.subheader("Parámetros de Producción")
        prod_col1, prod_col2 = st.columns(2)

        # Parámetros de producción
        production_params = {}

        with prod_col1:
            production_params["unidades_por_minuto"] = st.number_input("Unidades por Minuto",
                                                                       min_value=1, value=48, step=1, key="new_upm")
            production_params["peso_por_unidad"] = st.number_input("Peso por Unidad (gramos)",
                                                                   min_value=0.01, value=45.3, step=0.1, key="new_peso")

        with prod_col2:
            # Para máquinas Manual y Semi-Automática necesitamos el ratio productivo
            if machine_type in ["Manual", "Semi-Automática"]:
                st.write("Tiempo de Ciclo Productivo:")
                cycle_seconds = st.number_input("Duración del Ciclo (segundos)",
                                                min_value=1, value=32, step=1, key="new_cycle_time")
                productive_seconds = st.number_input("Tiempo Productivo del Ciclo (segundos)",
                                                     min_value=1, max_value=cycle_seconds, value=27, step=1,
                                                     key="new_productive_time")

                production_params["ciclo_total"] = cycle_seconds
                production_params["ciclo_productivo"] = productive_seconds
                production_params["ratio_productivo"] = productive_seconds / cycle_seconds
            else:
                # Para máquinas Automáticas, el ratio es siempre 1
                production_params["ratio_productivo"] = 1.0

        # Botón para guardar la configuración
        if st.button("Guardar Configuración", key="save_new_machine"):
            if not machine_name:
                st.error("⛔ Error: El nombre de la máquina es obligatorio")
            else:
                # Crear la configuración de la máquina
                machine_config = {
                    "name": machine_name,
                    "type": machine_type,
                    "description": machine_description,
                    "setup_params": setup_params,
                    "production_params": production_params,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Guardar en session_state
                st.session_state.machines[machine_name] = machine_config
                save_configurations()

                st.success(f"✅ Máquina '{machine_name}' configurada correctamente")
                st.rerun()

    # Lista de máquinas configuradas
    st.header("🔧 Máquinas Configuradas")

    if not st.session_state.machines:
        st.info("No hay máquinas configuradas. Agrega una nueva máquina usando el formulario de arriba.")
    else:
        # Mostrar las máquinas en una cuadrícula
        machine_cols = st.columns(3)
        for i, (name, config) in enumerate(st.session_state.machines.items()):
            col_idx = i % 3

            # Determinar la clase CSS según el tipo de máquina
            machine_class = ""
            if config["type"] == "Manual":
                machine_class = "machine-manual"
            elif config["type"] == "Semi-Automática":
                machine_class = "machine-semi"
            else:
                machine_class = "machine-auto"

            with machine_cols[col_idx]:
                # Crear tarjeta de máquina
                st.markdown(f"""
                <div class="machine-card {machine_class}">
                    <h3>{name}</h3>
                    <p><strong>Tipo:</strong> {config["type"]}</p>
                    <p><strong>Descripción:</strong> {config["description"] or "N/A"}</p>
                    <p><strong>Creada:</strong> {config["created_at"]}</p>
                </div>
                """, unsafe_allow_html=True)

                # Botones de acción
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🗑️ Eliminar", key=f"delete_{name}"):
                        # Confirmar eliminación
                        if name in st.session_state.machines:
                            del st.session_state.machines[name]
                            save_configurations()
                            st.success(f"Máquina '{name}' eliminada correctamente")
                            st.rerun()

                with col2:
                    if st.button("✏️ Editar", key=f"edit_{name}"):
                        st.session_state.editing_machine = name
                        st.rerun()

    # Formulario de edición de máquina
    if 'editing_machine' in st.session_state and st.session_state.editing_machine:
        machine_name = st.session_state.editing_machine
        machine_config = st.session_state.machines[machine_name]

        st.header(f"✏️ Editar Máquina: {machine_name}")

        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Nombre de la Máquina", value=machine_name, key="edit_machine_name")
            machine_type = st.selectbox("Tipo de Máquina", options=MACHINE_TYPES,
                                        index=MACHINE_TYPES.index(machine_config["type"]), key="edit_machine_type")

        with col2:
            machine_description = st.text_area("Descripción", value=machine_config.get("description", ""),
                                               key="edit_machine_description")

        st.subheader("Parámetros de Setup")
        setup_col1, setup_col2 = st.columns(2)

        # Editar parámetros de setup
        setup_params = {}
        setup_config = machine_config["setup_params"]

        with setup_col1:
            # Parámetros comunes a todos los tipos
            setup_params["calibracion"] = st.number_input("Tiempo de Calibración (min)",
                                                          min_value=0, value=setup_config.get("calibracion", 10),
                                                          step=1, key="edit_calibracion")
            setup_params["otros"] = st.number_input("Tiempo de Otros (min)",
                                                    min_value=0, value=setup_config.get("otros", 30),
                                                    step=1, key="edit_otros")
            setup_params["cambio_rollo"] = st.number_input("Tiempo de Cambio de Rollo (min)",
                                                           min_value=0, value=setup_config.get("cambio_rollo", 4),
                                                           step=1, key="edit_cambio_rollo")
            setup_params["cambio_producto"] = st.number_input("Tiempo de Cambio de Producto (min)",
                                                              min_value=0,
                                                              value=setup_config.get("cambio_producto", 15),
                                                              step=1, key="edit_cambio_producto")

        with setup_col2:
            # Parámetros específicos para Manual y Semi-Automática
            if machine_type in ["Manual", "Semi-Automática"]:
                setup_params["cambio_cuchillo"] = st.number_input("Tiempo de Cambio de Cuchillo (min)",
                                                                  min_value=0,
                                                                  value=setup_config.get("cambio_cuchillo", 30),
                                                                  step=1, key="edit_cambio_cuchillo")
                setup_params["cambio_perforador"] = st.number_input("Tiempo de Cambio de Perforador (min)",
                                                                    min_value=0,
                                                                    value=setup_config.get("cambio_perforador", 10),
                                                                    step=1, key="edit_cambio_perforador")
                setup_params["cambio_paquete"] = st.number_input("Tiempo de Cambio de Paquete (min)",
                                                                 min_value=0,
                                                                 value=setup_config.get("cambio_paquete", 5),
                                                                 step=1, key="edit_cambio_paquete")

            # Parámetro específico para Manual
            if machine_type == "Manual":
                setup_params["empaque"] = st.number_input("Tiempo de Empaque (segundos)",
                                                          min_value=0, value=setup_config.get("empaque", 60),
                                                          step=5, key="edit_empaque")

        st.subheader("Parámetros de Producción")
        prod_col1, prod_col2 = st.columns(2)

        # Editar parámetros de producción
        production_params = {}
        prod_config = machine_config["production_params"]

        with prod_col1:
            production_params["unidades_por_minuto"] = st.number_input("Unidades por Minuto",
                                                                       min_value=1,
                                                                       value=prod_config.get("unidades_por_minuto", 48),
                                                                       step=1, key="edit_upm")
            production_params["peso_por_unidad"] = st.number_input("Peso por Unidad (gramos)",
                                                                   min_value=0.01,
                                                                   value=prod_config.get("peso_por_unidad", 45.3),
                                                                   step=0.1, key="edit_peso")

        with prod_col2:
            # Para máquinas Manual y Semi-Automática necesitamos el ratio productivo
            if machine_type in ["Manual", "Semi-Automática"]:
                st.write("Tiempo de Ciclo Productivo:")
                cycle_seconds = st.number_input("Duración del Ciclo (segundos)",
                                                min_value=1, value=prod_config.get("ciclo_total", 32),
                                                step=1, key="edit_cycle_time")
                productive_seconds = st.number_input("Tiempo Productivo del Ciclo (segundos)",
                                                     min_value=1, max_value=cycle_seconds,
                                                     value=min(prod_config.get("ciclo_productivo", 27), cycle_seconds),
                                                     step=1, key="edit_productive_time")

                production_params["ciclo_total"] = cycle_seconds
                production_params["ciclo_productivo"] = productive_seconds
                production_params["ratio_productivo"] = productive_seconds / cycle_seconds
            else:
                # Para máquinas Automáticas, el ratio es siempre 1
                production_params["ratio_productivo"] = 1.0

        # Botones para guardar o cancelar
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Guardar Cambios", key="save_edit_machine"):
                if not new_name:
                    st.error("⛔ Error: El nombre de la máquina es obligatorio")
                else:
                    # Actualizar la configuración
                    updated_config = {
                        "name": new_name,
                        "type": machine_type,
                        "description": machine_description,
                        "setup_params": setup_params,
                        "production_params": production_params,
                        "created_at": machine_config.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Si el nombre cambió, eliminar la antigua entrada y crear una nueva
                    if new_name != machine_name:
                        del st.session_state.machines[machine_name]
                        st.session_state.machines[new_name] = updated_config
                    else:
                        st.session_state.machines[machine_name] = updated_config

                    save_configurations()
                    st.session_state.pop('editing_machine', None)
                    st.success(f"✅ Máquina '{new_name}' actualizada correctamente")
                    st.rerun()

        with col2:
            if st.button("Cancelar", key="cancel_edit_machine"):
                st.session_state.pop('editing_machine', None)
                st.rerun()


def production_calculator_page():
    """Página para calcular la producción usando máquinas configuradas"""
    st.title("🏭 Calculadora de Producción")

    # Verificar si hay máquinas configuradas
    if not st.session_state.machines:
        st.warning("⚠️ No hay máquinas configuradas. Por favor, configura al menos una máquina primero.")
        if st.button("Ir a Configuración de Máquinas"):
            st.session_state.current_page = "configuration"
            st.rerun()
        return

    # Seleccionar máquina
    machine_names = list(st.session_state.machines.keys())
    selected_machine = st.selectbox("Seleccione una Máquina", options=machine_names)
    machine_config = st.session_state.machines[selected_machine]

    # Mostrar información de la máquina seleccionada
    st.header(f"🔧 {selected_machine} - {machine_config['type']}")
    if machine_config.get("description"):
        st.info(machine_config["description"])

    # Parámetros de operación
    with st.expander("🔧 Configuración Operativa", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            turno_horas = st.number_input(
                "Duración del Turno (horas)",
                min_value=1.0, max_value=24.0, value=8.0, step=0.5
            )
            desayuno = st.checkbox("Incluir desayuno (15 min)")
            almuerzo = st.checkbox("Incluir almuerzo (60 min)")

        with col2:
            # Variables de interrupciones según el tipo de máquina
            interrupciones = {}

            # Cambios de rollo y producto son comunes a todos los tipos
            interrupciones["cambios_rollo"] = st.number_input(
                "Cambios de rollo", min_value=0, max_value=100, value=0, step=1
            )
            interrupciones["cambios_producto"] = st.number_input(
                "Cambios de producto", min_value=0, max_value=100, value=0, step=1
            )

            # Cambios específicos según el tipo de máquina
            if machine_config["type"] in ["Manual", "Semi-Automática"]:
                interrupciones["cambios_cuchillo"] = st.number_input(
                    "Cambios de cuchillo", min_value=0, max_value=100, value=0, step=1
                )
                interrupciones["cambios_perforador"] = st.number_input(
                    "Cambios de perforador", min_value=0, max_value=100, value=0, step=1
                )
                interrupciones["cambios_paquete"] = st.number_input(
                    "Cambios de paquete", min_value=0, max_value=100, value=0, step=1
                )

            if machine_config["type"] == "Manual":
                interrupciones["cambios_empaque"] = st.number_input(
                    "Cambios de empaque", min_value=0, max_value=100, value=0, step=1
                )

    # Obtener parámetros de la máquina
    setup_params = machine_config["setup_params"]
    production_params = machine_config["production_params"]

    # Cálculo de tiempos
    turno_minutos = turno_horas * 60

    # Interrupciones fijas
    interrupciones_fijas = setup_params.get("calibracion", 10) + setup_params.get("otros", 30) + (
        15 if desayuno else 0) + (60 if almuerzo else 0)

    # Interrupciones variables basadas en los parámetros de setup
    interrupciones_variables = 0
    for key, value in interrupciones.items():
        if key == "cambios_rollo" and value > 0:
            interrupciones_variables += value * setup_params.get("cambio_rollo", 4)
        elif key == "cambios_producto" and value > 0:
            interrupciones_variables += value * setup_params.get("cambio_producto", 15)
        elif key == "cambios_cuchillo" and value > 0:
            interrupciones_variables += value * setup_params.get("cambio_cuchillo", 30)
        elif key == "cambios_perforador" and value > 0:
            interrupciones_variables += value * setup_params.get("cambio_perforador", 10)
        elif key == "cambios_paquete" and value > 0:
            interrupciones_variables += value * setup_params.get("cambio_paquete", 5)
        elif key == "cambios_empaque" and value > 0:
            # Convertir tiempo de empaque de segundos a minutos para los cálculos
            interrupciones_variables += value * (setup_params.get("empaque", 60) / 60)

    tiempo_neto = turno_minutos - (interrupciones_fijas + interrupciones_variables)

    if tiempo_neto <= 0:
        st.error("⛔ Error: El tiempo de interrupciones excede la duración del turno")
        return

    # Ajuste por ratio productivo
    ratio_productivo = production_params.get("ratio_productivo", 1.0)
    tiempo_efectivo = tiempo_neto * ratio_productivo
    tiempo_detenido_ciclos = tiempo_neto * (1 - ratio_productivo)

    # Cálculo de producción
    unidades_por_minuto = production_params.get("unidades_por_minuto", 48)
    peso_por_unidad_g = production_params.get("peso_por_unidad", 45.3)

    unidades = unidades_por_minuto * tiempo_efectivo
    peso_kg = unidades * peso_por_unidad_g / 1000

    # Cálculo de eficiencia
    eficiencia = (tiempo_efectivo / turno_minutos) * 100

    # Resultados principales
    st.success("📈 Resultados de Producción")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Unidades Estimadas", f"{unidades:,.0f}",
                  delta=f"Rango: {unidades * 0.96:,.0f} - {unidades * 1.04:,.0f}")
    with col2:
        st.metric("Peso Total Estimado", f"{peso_kg:,.1f} kg",
                  delta=f"Rango: {peso_kg * 0.96:,.1f} - {peso_kg * 1.04:,.1f} kg")

    # Análisis de tiempos
    st.subheader("⏳ Análisis de Tiempos")
    tiempo_perdido = turno_minutos - tiempo_efectivo
    analysis_html = render_analysis_table(turno_minutos, tiempo_efectivo, tiempo_perdido, eficiencia)
    with st.expander("Ver Análisis de Tiempos", expanded=True):
        st.markdown(analysis_html, unsafe_allow_html=True)

    # Detalle de interrupciones
    interrupciones_dict = {
        "Calibración": setup_params.get("calibracion", 10),
        "Otros": setup_params.get("otros", 30),
        "Comidas": (15 if desayuno else 0) + (60 if almuerzo else 0)
    }

    # Agregar interrupciones variables
    for key, value in interrupciones.items():
        if key == "cambios_rollo" and value > 0:
            interrupciones_dict["Cambios Rollo"] = value * setup_params.get("cambio_rollo", 4)
        elif key == "cambios_producto" and value > 0:
            interrupciones_dict["Cambios Producto"] = value * setup_params.get("cambio_producto", 15)
        elif key == "cambios_cuchillo" and value > 0:
            interrupciones_dict["Cambios Cuchillo"] = value * setup_params.get("cambio_cuchillo", 30)
        elif key == "cambios_perforador" and value > 0:
            interrupciones_dict["Cambios Perforador"] = value * setup_params.get("cambio_perforador", 10)
        elif key == "cambios_paquete" and value > 0:
            interrupciones_dict["Cambios Paquete"] = value * setup_params.get("cambio_paquete", 5)
        elif key == "cambios_empaque" and value > 0:
            # Convertir tiempo de empaque de segundos a minutos para mostrar en la tabla
            interrupciones_dict["Cambios Empaque"] = value * (setup_params.get("empaque", 60) / 60)

    # Añadir tiempo de paradas automáticas si aplica
    if machine_config["type"] in ["Manual", "Semi-Automática"] and tiempo_detenido_ciclos > 0:
        interrupciones_dict["Paradas Automáticas"] = tiempo_detenido_ciclos

    with st.expander("🔍 Detalle de Interrupciones", expanded=False):
        interruptions_html = render_interruptions_table(interrupciones_dict, turno_minutos)
        st.markdown(interruptions_html, unsafe_allow_html=True)


def main():
    """Función principal de la aplicación"""
    # Sidebar para navegación
    with st.sidebar:
        st.title("🏭 Calculadora de Producción")
        st.markdown("---")

        # Navegación
        if st.button("🧮 Calculadora", use_container_width=True):
            st.session_state.current_page = "calculator"
            st.rerun()

        if st.button("⚙️ Configurar Máquinas", use_container_width=True):
            st.session_state.current_page = "configuration"
            st.rerun()

        st.markdown("---")


    # Mostrar la página correspondiente
    if st.session_state.current_page == "calculator":
        production_calculator_page()
    else:
        machine_configuration_page()


if __name__ == "__main__":
    main()