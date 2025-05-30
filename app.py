from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
import datetime

app = Flask(__name__)
app.secret_key = 'atm_secret_key'
DATA_FILE = 'users.csv'
TRANSACTIONS_FILE = 'transactions.csv'

def load_users():
    users = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['pin']] = {
                    'name': row['name'],
                    'balance': float(row['balance']),
                    'blocked': row.get('blocked', '0') == '1'
                }
    return users

def save_users(users):
    with open(DATA_FILE, mode='w', newline='') as file:
        fieldnames = ['pin', 'name', 'balance', 'blocked']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for pin, data in users.items():
            writer.writerow({
                'pin': pin,
                'name': data['name'],
                'balance': data['balance'],
                'blocked': '1' if data.get('blocked', False) else '0'
            })

def add_transaction(pin, type_, description, amount):
    file_exists = os.path.exists(TRANSACTIONS_FILE)
    with open(TRANSACTIONS_FILE, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['pin', 'date', 'type', 'description', 'amount'])
        if not file_exists:
            writer.writeheader()
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow({
            'pin': pin,
            'date': now,
            'type': type_,
            'description': description,
            'amount': amount
        })

def get_transactions(pin):
    transactions = []
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['pin'] == pin:
                    row['amount'] = float(row['amount'])
                    transactions.append(row)
    return transactions

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form['pin']
        name = request.form['name']
        users = load_users()
        user = users.get(pin)
        if user and user['name'].strip().lower() == name.strip().lower():
            session['user'] = pin
            return redirect(url_for('dashboard'))
        else:
            flash("PIN o nome non valido. Riprova.")
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
    users = load_users()
    if users[session['user']].get('blocked', False):
        return render_template('message.html', message="Carta bloccata. Operazione non consentita.")
    amount = float(request.form['amount'])
    if amount <= 0:
        return render_template('message.html', message="Importo non valido.")
    users[session['user']]['balance'] += amount
    save_users(users)
    add_transaction(session['user'], 'Deposito', 'Deposito contanti', amount)
    return render_template('message.html', message=f"Deposito di €{amount:.2f} completato.")

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    if users[session['user']].get('blocked', False):
        return render_template('message.html', message="Carta bloccata. Operazione non consentita.")
    amount = float(request.form['amount'])
    if amount <= 0:
        return render_template('message.html', message="Importo non valido.")
    if users[session['user']]['balance'] >= amount:
        users[session['user']]['balance'] -= amount
        save_users(users)
        add_transaction(session['user'], 'Prelievo', 'Prelievo contanti', -amount)
        return render_template('message.html', message=f"Prelievo di €{amount:.2f} effettuato.")
    else:
        return render_template('message.html', message="Saldo insufficiente.")

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    if users[session['user']].get('blocked', False):
        return render_template('message.html', message="Carta bloccata. Operazione non consentita.")

    if request.method == 'POST':
        recipient_pin = request.form['recipient']
        amount = float(request.form['amount'])

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

        add_transaction(sender_pin, 'Bonifico inviato', f'A {recipient_pin}', -amount)
        add_transaction(recipient_pin, 'Bonifico ricevuto', f'Da {sender_pin}', amount)

        return render_template('message.html', message=f"Bonifico di €{amount:.2f} inviato a {recipient_pin}.")

    return render_template('transfer.html')

@app.route('/recharge_phone', methods=['GET', 'POST'])
def recharge_phone():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    user = users[session['user']]
    if user.get('blocked', False):
        return render_template('message.html', message="Carta bloccata. Operazione non consentita.")
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        amount = float(request.form['amount'])
        if amount <= 0:
            return render_template('message.html', message="Importo non valido.")
        if user['balance'] < amount:
            return render_template('message.html', message="Saldo insufficiente per la ricarica.")
        users[session['user']]['balance'] -= amount
        save_users(users)
        add_transaction(session['user'], 'Ricarica telefonica', f'Numero: {phone_number}', -amount)
        return render_template('message.html', message=f"Ricarica di €{amount:.2f} effettuata sul numero {phone_number}.")
    return render_template('recharge_phone.html')

@app.route('/transactions')
def transactions():
    if 'user' not in session:
        return redirect(url_for('login'))
    txs = get_transactions(session['user'])
    return render_template('transactions.html', transactions=txs)

@app.route('/block_card', methods=['GET', 'POST'])
def block_card():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    user = users[session['user']]
    message = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'block':
            users[session['user']]['blocked'] = True
            save_users(users)
            message = "Carta bloccata con successo."
        elif action == 'unblock':
            users[session['user']]['blocked'] = False
            save_users(users)
            message = "Carta sbloccata con successo."
        else:
            message = "Azione non valida."
        user = users[session['user']]
    return render_template('block_card.html', user=user, message=message)

@app.route('/change_pin', methods=['GET', 'POST'])
def change_pin():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = load_users()
    current_pin = session['user']
    user = users[current_pin]
    message = None
    if request.method == 'POST':
        old_pin = request.form['old_pin']
        new_pin = request.form['new_pin']
        confirm_pin = request.form['confirm_pin']
        if old_pin != current_pin:
            message = "PIN attuale errato."
        elif not new_pin.isdigit() or len(new_pin) != 4:
            message = "Il nuovo PIN deve essere composto da 4 cifre."
        elif new_pin != confirm_pin:
            message = "I PIN non coincidono."
        elif new_pin in users:
            message = "Questo PIN è già in uso da un altro utente."
        else:
            users[new_pin] = users.pop(current_pin)
            save_users(users)
            session['user'] = new_pin
            message = "PIN cambiato con successo."
            return render_template('message.html', message=message)
    return render_template('change_pin.html', user=user, message=message)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)