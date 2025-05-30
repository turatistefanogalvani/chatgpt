from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os

app = Flask(__name__)
app.secret_key = 'atm_secret_key'
DATA_FILE = 'users.csv'

def load_users():
    users = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['pin']] = {
                    'name': row['name'],
                    'balance': float(row['balance'])
                }
    return users

def save_users(users):
    with open(DATA_FILE, mode='w', newline='') as file:
        fieldnames = ['pin', 'name', 'balance']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for pin, data in users.items():
            writer.writerow({'pin': pin, 'name': data['name'], 'balance': data['balance']})

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form['pin']
        users = load_users()
        user = users.get(pin)
        if user:
            session['user'] = pin
            return redirect(url_for('dashboard'))
        else:
            flash("PIN non valido. Riprova.")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    user = users[session['user']]
    return render_template('dashboard.html', user=user)

@app.route('/deposit', methods=['POST'])
def deposit():
    if 'user' not in session:
        return redirect(url_for('login'))
    amount = float(request.form['amount'])
    users = load_users()
    if amount <= 0:
        return render_template('message.html', message="Importo non valido.")
    users[session['user']]['balance'] += amount
    save_users(users)
    return render_template('message.html', message=f"Deposito di €{amount:.2f} completato.")

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session:
        return redirect(url_for('login'))
    amount = float(request.form['amount'])
    users = load_users()
    if amount <= 0:
        return render_template('message.html', message="Importo non valido.")
    if users[session['user']]['balance'] >= amount:
        users[session['user']]['balance'] -= amount
        save_users(users)
        return render_template('message.html', message=f"Prelievo di €{amount:.2f} effettuato.")
    else:
        return render_template('message.html', message="Saldo insufficiente.")

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipient_pin = request.form['recipient']
        amount = float(request.form['amount'])

        users = load_users()
        sender_pin = session['user']

        if recipient_pin not in users:
            return render_template('message.html', message="PIN destinatario non trovato.")
        if amount <= 0:
            return render_template('message.html', message="Importo non valido.")
        if users[sender_pin]['balance'] < amount:
            return render_template('message.html', message="Saldo insufficiente per il bonifico.")

        # Effettua il bonifico
        users[sender_pin]['balance'] -= amount
        users[recipient_pin]['balance'] += amount
        save_users(users)

        return render_template('message.html', message=f"Bonifico di €{amount:.2f} inviato a {recipient_pin}.")

    return render_template('transfer.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
