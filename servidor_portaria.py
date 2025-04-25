from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sqlite3
from datetime import datetime

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/cadastrar':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                nome = data['nome']
                cpf = data['cpf']
                bloco = data['bloco']
                apartamento = data['apartamento']
                tipo = data['tipo']
                placa = data.get('placa')

                conn = sqlite3.connect('portaria.db')
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO cadastros (nome, cpf, bloco, apartamento, placa, tipo, horario)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (nome, cpf, bloco, apartamento, placa, tipo, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    response = {"message": "Cadastro realizado com sucesso!"}
                    self.send_response(200)
                except sqlite3.IntegrityError:
                    response = {"message": "Erro: CPF já cadastrado!"}
                    self.send_response(409) # Código para conflito
                except sqlite3.Error as e:
                    response = {"message": f"Erro no banco de dados: {str(e)}"}
                    self.send_response(500) # Código para erro interno do servidor
                finally:
                    conn.close()

            except json.JSONDecodeError:
                response = {"message": "Erro: Dados JSON inválidos!"}
                self.send_response(400) # Código para requisição inválida
            except KeyError as e:
                response = {"message": f"Erro: Campo obrigatório ausente: {str(e)}"}
                self.send_response(400)

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        if self.path == '/listar':
            conn = sqlite3.connect('portaria.db')
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT nome, cpf, bloco, apartamento, tipo, placa, horario FROM cadastros")
                cadastros = cursor.fetchall()
                # Formatar a resposta como uma lista de dicionários
                response_data = []
                column_names = [description[0] for description in cursor.description]
                for cadastro in cadastros:
                    response_data.append(dict(zip(column_names, cadastro)))
                response = response_data
                self.send_response(200)
            except sqlite3.Error as e:
                response = {"message": f"Erro ao listar cadastros: {str(e)}"}
                self.send_response(500)
            finally:
                conn.close()

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Rota não encontrada!"}).encode('utf-8'))

def run_server():
    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Servidor rodando em http://{server_address[0]}:{server_address[1]}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor interrompido.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()