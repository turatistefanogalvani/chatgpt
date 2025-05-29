from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Dati esempio utenti
users = {
    "user1": {
        "pin": "1234",
        "saldo": 1000.0,
        "plafond": 5000.0,
        "carta_bloccata": False,
        "movimenti": []
    },
    "user2": {
        "pin": "5678",
        "saldo": 2000.0,
        "plafond": 3000.0,
        "carta_bloccata": False,
        "movimenti": []
    }
}

# Funzione per aggiungere movimenti
def add_movimento(user, tipo, descrizione, importo):
    users[user]["movimenti"].append({
        "tipo": tipo,
        "descrizione": descrizione,
        "importo": importo
    })

def is_logged():
    return 'user' in session and session['user'] in users and not users[session['user']]["carta_bloccata"]

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        pin = request.form.get('pin')
        if username in users:
            if users[username]["carta_bloccata"]:
                flash("Carta bloccata, contattare la banca")
            elif users[username]["pin"] == pin:
                session['user'] = username
                flash("Login effettuato")
                return redirect(url_for('dashboard'))
            else:
                flash("PIN errato")
        else:
            flash("Utente non trovato")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logout effettuato")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not is_logged():
        flash("Devi effettuare il login")
        return redirect(url_for('login'))
    user = session['user']
    return render_template(
        'dashboard.html',
        user=user,
        saldo=users[user]['saldo'],
        plafond=users[user]['plafond'],
        bloccata=users[user]['carta_bloccata'],
        balance=users[user]['saldo']  # aggiunto per compatibilità con il template
    )

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('withdraw'))
        if amount <= 0:
            flash("Importo deve essere positivo")
        elif amount > users[user]['saldo']:
            flash("Saldo insufficiente")
        else:
            users[user]['saldo'] -= amount
            add_movimento(user, "Prelievo", "Prelievo contanti", -amount)
            flash(f"Prelievo di {amount:.2f}€ effettuato")
            return redirect(url_for('dashboard'))
    return render_template('withdraw.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('deposit'))
        if amount <= 0:
            flash("Importo deve essere positivo")
        else:
            users[user]['saldo'] += amount
            add_movimento(user, "Deposito", "Deposito contanti", amount)
            flash(f"Deposito di {amount:.2f}€ effettuato")
            return redirect(url_for('dashboard'))
    return render_template('deposit.html')

@app.route('/deposit_checks', methods=['GET', 'POST'])
def deposit_checks():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('deposit_checks'))
        if amount <= 0:
            flash("Importo deve essere positivo")
        else:
            users[user]['saldo'] += amount
            add_movimento(user, "Deposito assegni", "Deposito assegni", amount)
            flash(f"Deposito assegni di {amount:.2f}€ effettuato")
            return redirect(url_for('dashboard'))
    return render_template('deposit_checks.html')

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    commissione = 1.50
    if request.method == 'POST':
        destinatario = request.form.get('destinatario')
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('transfer'))
        totale = amount + commissione
        if destinatario not in users:
            flash("Destinatario inesistente")
        elif amount <= 0:
            flash("Importo deve essere positivo")
        elif totale > users[user]['saldo']:
            flash(f"Saldo insufficiente (inclusa commissione {commissione}€)")
        else:
            users[user]['saldo'] -= totale
            users[destinatario]['saldo'] += amount
            add_movimento(user, "Bonifico", f"Bonifico a {destinatario} (commissione {commissione}€)", -totale)
            add_movimento(destinatario, "Bonifico ricevuto", f"Bonifico da {user}", amount)
            flash(f"Bonifico di {amount:.2f}€ inviato a {destinatario} (commissione {commissione}€)")
            return redirect(url_for('dashboard'))
    return render_template('transfer.html')

@app.route('/payments', methods=['GET', 'POST'])
def payments():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('payments'))
        description = request.form.get('description')
        if amount <= 0:
            flash("Importo deve essere positivo")
        elif amount > users[user]['saldo']:
            flash("Saldo insufficiente")
        else:
            users[user]['saldo'] -= amount
            add_movimento(user, "Pagamento", description, -amount)
            flash(f"Pagamento '{description}' di {amount:.2f}€ effettuato")
            return redirect(url_for('dashboard'))
    return render_template('payments.html')

@app.route('/recharge_phone', methods=['GET', 'POST'])
def recharge_phone():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('recharge_phone'))
        phone_number = request.form.get('phone_number')
        if amount <= 0:
            flash("Importo deve essere positivo")
        elif amount > users[user]['saldo']:
            flash("Saldo insufficiente")
        else:
            users[user]['saldo'] -= amount
            add_movimento(user, "Ricarica telefonica", f"Ricarica a {phone_number}", -amount)
            flash(f"Ricarica telefonica di {amount:.2f}€ effettuata al numero {phone_number}")
            return redirect(url_for('dashboard'))
    return render_template('recharge_phone.html')

@app.route('/change_pin', methods=['GET', 'POST'])
def change_pin():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        old_pin = request.form.get('old_pin')
        new_pin = request.form.get('new_pin')
        confirm_pin = request.form.get('confirm_pin')
        if old_pin != users[user]['pin']:
            flash("PIN attuale errato")
        elif new_pin != confirm_pin:
            flash("Nuovo PIN e conferma non coincidono")
        elif len(new_pin) < 4:
            flash("PIN deve essere almeno 4 cifre")
        else:
            users[user]['pin'] = new_pin
            flash("PIN cambiato con successo")
            return redirect(url_for('dashboard'))
    return render_template('change_pin.html')

@app.route('/block_card', methods=['GET', 'POST'])
def block_card():
    if not is_logged():
        flash("Login richiesto")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        users[user]["carta_bloccata"] = True
        flash("Carta bloccata. Contatta la banca per riattivarla.")
        return redirect(url_for('logout'))
    return render_template('block_card.html')

@app.route('/info')
def info():
    if not is_logged():
        flash("Login richiesto")
        return redirect(url_for('login'))
    user = session['user']
    saldo = users[user]['saldo']
    plafond = users[user]['plafond']
    return render_template('info.html', saldo=saldo, plafond=plafond)

@app.route('/foreign_currency_withdraw', methods=['GET', 'POST'])
def foreign_currency_withdraw():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    rates = {'USD': 1.1, 'GBP': 0.9, 'CHF': 1.0}  # Esempio tassi di cambio
    if request.method == 'POST':
        currency = request.form.get('currency')
        try:
            amount_foreign = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('foreign_currency_withdraw'))
        if amount_foreign <= 0:
            flash("Importo deve essere positivo")
            return redirect(url_for('foreign_currency_withdraw'))
        if currency not in rates:
            flash("Valuta non supportata")
            return redirect(url_for('foreign_currency_withdraw'))
        amount_eur = amount_foreign / rates[currency]
        if amount_eur > users[user]['saldo']:
            flash("Saldo insufficiente")
            return redirect(url_for('foreign_currency_withdraw'))
        users[user]['saldo'] -= amount_eur
        add_movimento(user, "Prelievo valuta estera", f"Prelievo {amount_foreign} {currency}", -amount_eur)
        flash(f"Prelievo di {amount_foreign:.2f} {currency} effettuato (equivalente a {amount_eur:.2f} €)")
        return redirect(url_for('dashboard'))
    return render_template('foreign_currency_withdraw.html', rates=rates)

@app.route('/prepaid_card_recharge', methods=['GET', 'POST'])
def prepaid_card_recharge():
    if not is_logged():
        flash("Login richiesto o carta bloccata")
        return redirect(url_for('login'))
    user = session['user']
    if request.method == 'POST':
        card_number = request.form.get('card_number')
        try:
            amount = float(request.form.get('amount'))
        except:
            flash("Importo non valido")
            return redirect(url_for('prepaid_card_recharge'))
        if amount <= 0:
            flash("Importo deve essere positivo")
        elif amount > users[user]['saldo']:
            flash("Saldo insufficiente")
        else:
            users[user]['saldo'] -= amount
            add_movimento(user, "Ricarica carta prepagata", f"Ricarica carta {card_number}", -amount)
            flash(f"Ricarica carta prepagata di {amount:.2f}€ effettuata per carta {card_number}")
            return redirect(url_for('dashboard'))
    return render_template('prepaid_card_recharge.html')

if __name__ == '__main__':
    app.run(debug=True)