from flask import Blueprint, render_template,session, redirect, url_for, request, send_file
from app.utils import utils
from app.services import service
from app.auth import login_required

import pandas as pd


report_bp = Blueprint("report", __name__)

@report_bp.route("/", methods=["GET"])
@report_bp.route("/login-page", methods=["GET"])
def login_page():
    if session.get("authorized"):
        # usuário já logado? manda pro home
        return redirect(url_for("report.home"))
    return render_template("auth/login.html")

@report_bp.route("/home", methods=["GET"])
@login_required
def home():
    return render_template("index.html")

@report_bp.route("/report/download", methods=["GET"])
@login_required
def download_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    range_date = utils.generate_date_range(start_date, end_date)


    output = service.generate_reports(range_date)

     # Dados fictícios para exemplo
    data = {
        "Data": [start_date, end_date],
        "Valor": [100, 200]
    }

    df = pd.DataFrame(data)



    # Nome do arquivo com datas
    filename = f"relatorio_{start_date}_{end_date}.xlsx"


    return send_file(
        output,
        as_attachment=True,
        download_name= filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )