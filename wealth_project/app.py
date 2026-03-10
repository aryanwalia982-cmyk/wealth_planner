from flask import Flask, render_template, request, redirect, session, make_response
import sqlite3
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = "wealth_secret_key"

latest_report = {}


def get_db_connection():
    conn = sqlite3.connect("wealth_app.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            recovery_code TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_users_table()


def format_inr(amount):
    return f"Rs. {amount:,.2f}"


def calculate_future_wealth(yearly_savings, annual_return, years):
    total = 0
    data = []

    for _ in range(years):
        total = (total + yearly_savings) * (1 + annual_return / 100)
        data.append(round(total, 2))

    return round(total, 2), data


def generate_ai_prediction(income, expenses, monthly_savings, return_rate, years, inflation_rate, wealth):
    savings_ratio = monthly_savings / income if income > 0 else 0

    if monthly_savings <= 0:
        summary = "Your expenses are too high compared to your income."
        wealth_score = 25
    elif savings_ratio < 0.2:
        summary = "Your financial base is weak right now, but it can improve with better saving habits."
        wealth_score = 45
    elif savings_ratio < 0.4:
        summary = "You are on a decent track and can build strong wealth with consistency."
        wealth_score = 70
    else:
        summary = "Your savings habit is strong and your long-term wealth potential looks very good."
        wealth_score = 85

    if years >= 10:
        wealth_score += 5
    if inflation_rate > 7:
        wealth_score -= 5
    if return_rate > 15:
        wealth_score -= 5

    wealth_score = max(1, min(100, wealth_score))

    safe_return = max(return_rate - 3, 4)
    balanced_return = return_rate
    aggressive_return = min(return_rate + 4, 18)

    tips = []

    if monthly_savings <= 0:
        tips.append("Reduce unnecessary monthly expenses immediately.")
    else:
        tips.append("Maintain a fixed monthly investment habit.")

    if savings_ratio < 0.2:
        tips.append("Try to save at least 20 percent of your monthly income.")
    else:
        tips.append("Increase your savings rate gradually every few months.")

    if years < 10:
        tips.append("A longer investment duration can improve compounding a lot.")
    else:
        tips.append("Stay patient and avoid breaking long-term investments early.")

    return {
        "summary": summary,
        "wealth_score": wealth_score,
        "safe_return": safe_return,
        "balanced_return": balanced_return,
        "aggressive_return": aggressive_return,
        "tips": tips
    }


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        recovery_code = request.form['recovery_code']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return "User already exists. Please login."

        cursor.execute(
            "INSERT INTO users (username, password, recovery_code) VALUES (?, ?, ?)",
            (username, password, recovery_code)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('signup.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user'] = username
        return redirect('/calculator')
    else:
        return "Invalid username or password."


@app.route('/calculator')
def calculator():
    if 'user' not in session:
        return redirect('/')
    return render_template('calculator.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    global latest_report

    if 'user' not in session:
        return redirect('/')

    try:
        income = float(request.form['income'])
        expenses = float(request.form['expenses'])
        return_rate = float(request.form['return_rate'])
        years = int(request.form['years'])
        inflation_rate = float(request.form['inflation_rate'])

        if income <= 0:
            return "Error: Income must be greater than 0."
        if expenses < 0:
            return "Error: Expenses cannot be negative."
        if expenses > income:
            return "Error: Expenses cannot be greater than income."
        if return_rate < 0 or return_rate > 100:
            return "Error: Return rate must be between 0 and 100."
        if years < 1 or years > 100:
            return "Error: Years must be between 1 and 100."
        if inflation_rate < 0 or inflation_rate > 50:
            return "Error: Inflation rate must be between 0 and 50."

        monthly_savings = income - expenses
        yearly_savings = monthly_savings * 12

        wealth = 0
        yearly_data = []
        year_labels = []
        wealth_table = []

        for i in range(1, years + 1):
            wealth = (wealth + yearly_savings) * (1 + return_rate / 100)
            rounded_wealth = round(wealth, 2)

            yearly_data.append(rounded_wealth)
            year_labels.append(f"Year {i}")
            wealth_table.append({
                "year": i,
                "wealth": format_inr(rounded_wealth)
            })

        inflation_adjusted_wealth = wealth / ((1 + inflation_rate / 100) ** years)

        if monthly_savings <= 0:
            advice = "Your expenses are too high. First focus on reducing expenses."
        elif monthly_savings < income * 0.2:
            advice = "Your savings are low. Try to save at least 20 percent of your income."
        else:
            advice = "Excellent! With discipline and investing, your wealth can grow strongly."

        ai_prediction = generate_ai_prediction(
            income,
            expenses,
            monthly_savings,
            return_rate,
            years,
            inflation_rate,
            round(wealth, 2)
        )

        safe_return = float(ai_prediction["safe_return"])
        balanced_return = float(ai_prediction["balanced_return"])
        aggressive_return = float(ai_prediction["aggressive_return"])

        safe_prediction, safe_data = calculate_future_wealth(yearly_savings, safe_return, years)
        balanced_prediction, balanced_data = calculate_future_wealth(yearly_savings, balanced_return, years)
        aggressive_prediction, aggressive_data = calculate_future_wealth(yearly_savings, aggressive_return, years)

        latest_report = {
            "monthly_savings": format_inr(monthly_savings),
            "yearly_savings": format_inr(yearly_savings),
            "wealth": format_inr(round(wealth, 2)),
            "inflation_adjusted_wealth": format_inr(round(inflation_adjusted_wealth, 2)),
            "return_rate": return_rate,
            "inflation_rate": inflation_rate,
            "years": years,
            "advice": advice,
            "ai_summary": ai_prediction["summary"],
            "wealth_score": ai_prediction["wealth_score"],
            "safe_prediction": format_inr(safe_prediction),
            "balanced_prediction": format_inr(balanced_prediction),
            "aggressive_prediction": format_inr(aggressive_prediction),
            "tips": ai_prediction["tips"],
            "wealth_table": wealth_table
        }

        return render_template(
            'result.html',
            monthly_savings=format_inr(monthly_savings),
            yearly_savings=format_inr(yearly_savings),
            wealth=format_inr(round(wealth, 2)),
            inflation_adjusted_wealth=format_inr(round(inflation_adjusted_wealth, 2)),
            return_rate=return_rate,
            inflation_rate=inflation_rate,
            years=years,
            advice=advice,
            yearly_data=yearly_data,
            year_labels=year_labels,
            wealth_table=wealth_table,
            ai_summary=ai_prediction["summary"],
            wealth_score=ai_prediction["wealth_score"],
            safe_prediction=format_inr(safe_prediction),
            balanced_prediction=format_inr(balanced_prediction),
            aggressive_prediction=format_inr(aggressive_prediction),
            tips=ai_prediction["tips"],
            safe_data=safe_data,
            balanced_data=balanced_data,
            aggressive_data=aggressive_data
        )

    except ValueError:
        return "Error: Please enter valid numeric values."


@app.route('/download-pdf')
def download_pdf():
    global latest_report

    if 'user' not in session:
        return redirect('/')

    if not latest_report:
        return "No report available. Please calculate wealth first."

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Wealth Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", "", 12)

    pdf.cell(200, 10, txt=f"Monthly Savings: {latest_report['monthly_savings']}", ln=True)
    pdf.cell(200, 10, txt=f"Yearly Savings: {latest_report['yearly_savings']}", ln=True)
    pdf.cell(200, 10, txt=f"Expected Annual Return: {latest_report['return_rate']}%", ln=True)
    pdf.cell(200, 10, txt=f"Inflation Rate: {latest_report['inflation_rate']}%", ln=True)
    pdf.cell(200, 10, txt=f"Investment Duration: {latest_report['years']} years", ln=True)
    pdf.cell(200, 10, txt=f"Estimated Future Wealth: {latest_report['wealth']}", ln=True)
    pdf.cell(200, 10, txt=f"Inflation Adjusted Wealth: {latest_report['inflation_adjusted_wealth']}", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="Advice:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, txt=latest_report['advice'])

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="AI Prediction Summary:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, txt=latest_report['ai_summary'])

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt=f"Wealth Score: {latest_report['wealth_score']}/100", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Safe Scenario: {latest_report['safe_prediction']}", ln=True)
    pdf.cell(200, 10, txt=f"Balanced Scenario: {latest_report['balanced_prediction']}", ln=True)
    pdf.cell(200, 10, txt=f"Aggressive Scenario: {latest_report['aggressive_prediction']}", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="AI Tips:", ln=True)
    pdf.set_font("Arial", "", 12)
    for tip in latest_report["tips"]:
        pdf.multi_cell(0, 10, txt=f"- {tip}")

    pdf.ln(8)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, txt="Yearly Wealth Breakdown:", ln=True)
    pdf.set_font("Arial", "", 12)
    for row in latest_report["wealth_table"]:
        pdf.cell(200, 8, txt=f"Year {row['year']}: {row['wealth']}", ln=True)

    pdf_output = pdf.output(dest='S').encode('latin-1')

    response = make_response(pdf_output)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=wealth_report.pdf'

    return response


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        recovery_code = request.form['recovery_code']
        new_password = request.form['new_password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND recovery_code = ?",
            (username, recovery_code)
        )
        user = cursor.fetchone()

        if user:
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                (new_password, username)
            )
            conn.commit()
            conn.close()
            return "Password reset successful. Go back and login."
        else:
            conn.close()
            return "Invalid username or recovery code."

    return render_template("forgot_password.html")


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)