from flask import Flask, render_template, request, send_file
import matplotlib.pyplot as plt
from fpdf import FPDF
import locale
from io import BytesIO
import base64

app = Flask(__name__)
locale.setlocale(locale.LC_ALL, '')

def calculate_sip(monthly_investment, annual_return, years, inflation):
    monthly_rate = annual_return / 100 / 12
    months = int(years * 12)
    future_value = 0
    total_invested = 0
    breakdown = []
    value_history = []
    
    for month in range(1, months + 1):
        future_value = (future_value + monthly_investment) * (1 + monthly_rate)
        total_invested += monthly_investment
        if month % 12 == 0 or month == months:
            breakdown.append({
                'year': (month - 1) // 12 + 1,
                'total_invested': locale.currency(total_invested, grouping=True),
                'future_value': locale.currency(future_value, grouping=True)
            })
        value_history.append(future_value)
    
    # Generate plot
    img = BytesIO()
    plt.figure(figsize=(10, 5))
    plt.plot([i/12 for i in range(1, months+1)], value_history, color='#3498db', linewidth=2)
    plt.title('Investment Growth Over Time', fontsize=14)
    plt.xlabel('Years', fontsize=12)
    plt.ylabel('Portfolio Value (₹)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(img, format='png', dpi=120)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    
    return {
        'future_value': locale.currency(future_value, grouping=True),
        'total_invested': locale.currency(total_invested, grouping=True),
        'breakdown': breakdown,
        'plot_url': plot_url
    }

def generate_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SIP Investment Report", ln=True, align='C')
    pdf.ln(10)
    
    # Results
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Future Value: {data['future_value']}", ln=True)
    pdf.cell(200, 10, txt=f"Total Invested: {data['total_invested']}", ln=True)
    pdf.ln(10)
    
    # Breakdown
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Yearly Breakdown:", ln=True)
    pdf.set_font("Arial", size=10)
    for entry in data['breakdown']:
        pdf.cell(200, 8, txt=f"Year {entry['year']}: {entry['future_value']} (Invested: {entry['total_invested']})", ln=True)
    
    pdf.output("report.pdf")
    return "report.pdf"

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        try:
            monthly_investment = float(request.form['monthly_investment'])
            annual_return = float(request.form['annual_return'])
            years = float(request.form['years'])
            inflation = float(request.form['inflation'])

            if monthly_investment <= 0 or annual_return <= 0 or years <= 0:
                raise ValueError("All values must be greater than zero")

            data = calculate_sip(monthly_investment, annual_return, years, inflation)
            return render_template('result.html', **data)
            
        except KeyError:
            error = "Missing fields - please fill all inputs"
        except ValueError as e:
            error = str(e)
        except Exception as e:
            return render_template('error.html', error=str(e))
    
    return render_template('index.html', error=error)

@app.route('/download', methods=['POST'])
def download():
    try:
        data = calculate_sip(
            float(request.form['monthly_investment']),
            float(request.form['annual_return']),
            float(request.form['years']),
            float(request.form['inflation'])
        )
        pdf_path = generate_pdf(data)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)