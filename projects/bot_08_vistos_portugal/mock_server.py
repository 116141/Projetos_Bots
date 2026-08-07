from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for, session
import io
import datetime

app = Flask(__name__)
app.secret_key = "local-test-secret"

# Simulated data: a simple in‑memory calendar with random availability
calendar = {
    # date: bool (True = slot available)
    "2026-08-15": True,
    "2026-08-16": False,
    "2026-08-17": True,
}

# Templates (inline for simplicity)
login_template = """
<!doctype html>
<title>Login Mock</title>
<h2>Login</h2>
<form method=post>
  Email: <input name=email type=text required><br>
  Senha: <input name=password type=password required><br>
  <button type=submit>Entrar</button>
</form>
{% if error %}<p style='color:red;'>{{ error }}</p>{% endif %}
"""

schedule_template = """
<!doctype html>
<title>Agendamento Mock</title>
<h2>Selecione a data</h2>
<ul>
{% for date, free in calendar.items() %}
  <li>
    {{ date }} - {% if free %}<a href='{{ url_for('confirm', date=date) }}'>Disponível</a>{% else %}<span style='color:gray;'>Indisponível</span>{% endif %}
  </li>
{% endfor %}
</ul>
"""

confirm_template = """
<!doctype html>
<title>Confirmação</title>
<h2>Confirmação de Agendamento</h2>
<p>Data selecionada: {{ date }}</p>
<form method=post>
  Nome: <input name=name required><br>
  Passaporte: <input name=passport required><br>
  Data de Nascimento: <input name=birth type=date required><br>
  Email: <input name=email type=email required><br>
  Telefone: <input name=phone required><br>
  <button type=submit>Confirmar</button>
</form>
"""

@app.route('/')
def index():
    if session.get('logged'):
        return redirect(url_for('schedule'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # em um teste real validaríamos contra a lista de contas; aqui aceitamos qualquer credencial
        if email and password:
            session['logged'] = True
            session['user'] = email
            return redirect(url_for('schedule'))
        error = "Credenciais inválidas"
    return render_template_string(login_template, error=error)

@app.route('/schedule')
def schedule():
    if not session.get('logged'):
        return redirect(url_for('login'))
    return render_template_string(schedule_template, calendar=calendar)

@app.route('/confirm/<date>', methods=['GET', 'POST'])
def confirm(date):
    if not session.get('logged'):
        return redirect(url_for('login'))
    if date not in calendar or not calendar[date]:
        return "Data indisponível", 404
    if request.method == 'POST':
        # Simular criação de PDF – geramos um PDF simples em memória
        pdf_bytes = generate_fake_pdf(date, request.form)
        filename = f"comprovante_{date}.pdf"
        # Marcar a data como ocupada
        calendar[date] = False
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
    return render_template_string(confirm_template, date=date)

def generate_fake_pdf(date_str: str, data: dict) -> bytes:
    """Cria um PDF de exemplo contendo os dados de agendamento.
    Para fins de teste usamos a biblioteca de geração de PDF simples (reportlab).
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError:
        # Se a dependência não estiver instalada, devolvemos um PDF vazio
        return b"%PDF-1.4\n%âãÏÓ\n1 0 obj\n<<>>\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer\n<<>>\n%%EOF"
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle('Comprovante de Agendamento')
    c.drawString(72, 750, f"Comprovante de Agendamento - {date_str}")
    y = 720
    for key, value in data.items():
        c.drawString(72, y, f"{key.capitalize()}: {value}")
        y -= 20
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

if __name__ == '__main__':
    # Executar em modo debug para facilitar testes locais
    app.run(host='127.0.0.1', port=5000, debug=True)
