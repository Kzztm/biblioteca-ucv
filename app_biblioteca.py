import psycopg2
import streamlit as st
import pandas as pd
from datetime import date


DATABASE_URL = "postgresql://neondb_owner:npg_QWilREt4STz9@ep-young-math-atsnaajd-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def obtener_conexion():
    return psycopg2.connect(DATABASE_URL)


def inicializar_bd():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Libros (
            id_libro SERIAL PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            autor VARCHAR(255) NOT NULL,
            estado VARCHAR(50) DEFAULT 'Disponible'
        )
    ''')
    
  
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Estudiantes (
            dni VARCHAR(8) PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL
        )
    ''')
    
   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Prestamos (
            id_prestamo SERIAL PRIMARY KEY,
            id_libro INTEGER REFERENCES Libros(id_libro),
            dni_estudiante VARCHAR(8) REFERENCES Estudiantes(dni),
            fecha_prestamo DATE,
            fecha_devolucion DATE
        )
    ''')
    
    conexion.commit()
    conexion.close()

inicializar_bd()


st.title("📚 Sistema de Biblioteca Universitaria")
st.write("Panel de control para registro y préstamo de material bibliográfico.")


st.sidebar.markdown("# 🏛️")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💻 Desarrollador:")
st.sidebar.markdown("**Miguel Hernán Talledo Talledo**")
st.sidebar.markdown("*Estudiante de Ingeniería de Sistemas*")
st.sidebar.markdown("📍 **UCV - Piura**")
st.sidebar.markdown("---")
menu = ["Registrar Libro", "Ver Inventario", "Registrar Estudiante", "Realizar Préstamo", "Ver Préstamos Activos"]
eleccion = st.sidebar.selectbox("Menú de Navegación", menu)


if eleccion == "Registrar Libro":
    st.subheader("Registrar Nuevo Ejemplar")
    with st.form(key='form_libro'):
        titulo = st.text_input("Título del libro")
        autor = st.text_input("Autor")
        if st.form_submit_button("Guardar Libro"):
            if titulo and autor:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute("INSERT INTO Libros (titulo, autor) VALUES (%s, %s)", (titulo, autor))
                conexion.commit()
                conexion.close()
                st.success(f"✅ Libro '{titulo}' registrado.")
            else:
                st.warning("⚠️ Llena todos los campos.")


elif eleccion == "Ver Inventario":
    st.subheader("Inventario Actual de la Biblioteca")
    conexion = obtener_conexion()
    df_libros = pd.read_sql_query("SELECT id_libro, titulo, autor, estado FROM Libros ORDER BY id_libro", conexion)
    conexion.close()
    if df_libros.empty:
        st.info("No hay libros registrados.")
    else:
        st.dataframe(df_libros, use_container_width=True, hide_index=True)


elif eleccion == "Registrar Estudiante":
    st.subheader("Alta de Nuevo Estudiante")
    with st.form(key='form_estudiante'):
        dni = st.text_input("DNI del Estudiante (8 dígitos)", max_chars=8)
        nombre = st.text_input("Nombre Completo")
        if st.form_submit_button("Guardar Estudiante"):
            if dni and nombre and len(dni) == 8:
                try:
                    conexion = obtener_conexion()
                    cursor = conexion.cursor()
                    cursor.execute("INSERT INTO Estudiantes (dni, nombre) VALUES (%s, %s)", (dni, nombre))
                    conexion.commit()
                    conexion.close()
                    st.success(f"✅ Estudiante {nombre} registrado con éxito.")
                except Exception as e:
                    st.error("Error: Es posible que este DNI ya esté registrado.")
            else:
                st.warning("⚠️ Revisa que el DNI tenga 8 dígitos y hayas puesto el nombre.")


elif eleccion == "Realizar Préstamo":
    st.subheader("Registrar Nuevo Préstamo")
    
    conexion = obtener_conexion()
    
    df_disponibles = pd.read_sql_query("SELECT id_libro, titulo FROM Libros WHERE estado = 'Disponible'", conexion)
    
    df_estudiantes = pd.read_sql_query("SELECT dni, nombre FROM Estudiantes", conexion)
    conexion.close()

    if df_disponibles.empty or df_estudiantes.empty:
        st.warning("⚠️ Necesitas tener al menos un libro disponible y un estudiante registrado para hacer un préstamo.")
    else:
        with st.form(key='form_prestamo'):
          
            opciones_libros = df_disponibles.apply(lambda row: f"{row['id_libro']} - {row['titulo']}", axis=1).tolist()
            opciones_estudiantes = df_estudiantes.apply(lambda row: f"{row['dni']} - {row['nombre']}", axis=1).tolist()
            
            libro_seleccionado = st.selectbox("Selecciona el Libro", opciones_libros)
            estudiante_seleccionado = st.selectbox("Selecciona el Estudiante", opciones_estudiantes)
            
            if st.form_submit_button("Confirmar Préstamo"):
                
                id_libro = libro_seleccionado.split(" - ")[0]
                dni_estudiante = estudiante_seleccionado.split(" - ")[0]
                fecha_hoy = date.today()

                conexion = obtener_conexion()
                cursor = conexion.cursor()
                
               
                cursor.execute("INSERT INTO Prestamos (id_libro, dni_estudiante, fecha_prestamo) VALUES (%s, %s, %s)", 
                               (id_libro, dni_estudiante, fecha_hoy))
               
                cursor.execute("UPDATE Libros SET estado = 'Prestado' WHERE id_libro = %s", (id_libro,))
                
                conexion.commit()
                conexion.close()
                st.success("✅ Préstamo registrado correctamente. El inventario ha sido actualizado.")


elif eleccion == "Ver Préstamos Activos":
    st.subheader("Historial de Préstamos")
    conexion = obtener_conexion()
   
    query = '''
        SELECT p.id_prestamo, l.titulo, e.nombre AS estudiante, p.fecha_prestamo 
        FROM Prestamos p
        JOIN Libros l ON p.id_libro = l.id_libro
        JOIN Estudiantes e ON p.dni_estudiante = e.dni
        WHERE p.fecha_devolucion IS NULL
    '''
    df_prestamos = pd.read_sql_query(query, conexion)
    conexion.close()
    
    if df_prestamos.empty:
        st.info("No hay préstamos activos en este momento.")
    else:
        st.dataframe(df_prestamos, use_container_width=True, hide_index=True)
