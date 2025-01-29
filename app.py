from flask import Flask, jsonify
import mysql.connector
import os

app = Flask(__name__)

# Configuración para Render
DB_CONFIG = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'ssl_ca': os.environ.get('MYSQL_SSL_CA') or None
}

@app.route('/cons_prov', methods=['GET'])
def consultar_proveedores():
    try:
        conexion = mysql.connector.connect(**DB_CONFIG)
        cursor = conexion.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT idprov, nom_emp, ruc, nom_per, telefono, 
                   correo, direccion, cond_pago, comp_gener 
            FROM proveedores
        """)
        
        resultados = cursor.fetchall()
        cursor.close()
        conexion.close()
        
        return jsonify({
            'proveedores': resultados,
            'total': len(resultados)
        }), 200
    
    except mysql.connector.Error as err:
        return jsonify({'error': f'Error MySQL: {err}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error general: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000))