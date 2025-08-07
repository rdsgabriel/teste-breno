import pandas as pd

from .api_medical_service_financial_report import bucket_calls_sync
from .api_export_medical_care import bucket_calls_sync_medical
from .data_processing import tables_dinamic
from io import BytesIO

BRMED_CLINIC=[1,5,6,9,10,11,14,15,16,17,18,19,20,22]

def generate_reports(range_date):

  response_medical_care = bucket_calls_sync(range_date)
  response_medical_care_time = bucket_calls_sync_medical(range_date,BRMED_CLINIC)
  
  report,preco_df, pacientes_df, exames_df,duracao_media_exames_df,profissionais_necessarios_df,alocacao_df,ocupacao_df = tables_dinamic(response_medical_care,response_medical_care_time)

  output = BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
      #Aba 1
      report.to_excel(writer, index = False,sheet_name='Exames', startrow= 0)
      #Aba 2
      preco_df.round(2).to_excel(writer, sheet_name='Tabelas Dinâmicas', startrow= 0)
      pacientes_df.round(2).to_excel(writer, sheet_name='Tabelas Dinâmicas', startrow= preco_df.shape[0] + 3)
      exames_df.round(2).to_excel(writer, sheet_name='Tabelas Dinâmicas', startrow=(preco_df.shape[0] +3)+(pacientes_df.shape[0] +3))
      #Aba 3
      duracao_media_exames_df.round(2).to_excel(writer, sheet_name='Produtividade', startrow= 0)
      profissionais_necessarios_df.round(2).to_excel(writer, sheet_name='Produtividade', startrow= duracao_media_exames_df.shape[0] + 3)
      alocacao_df.round(2).to_excel(writer, sheet_name='Produtividade', startrow= (duracao_media_exames_df.shape[0] +3)+(profissionais_necessarios_df.shape[0] +3))
      ocupacao_df.round(2).to_excel(writer, sheet_name='Produtividade', startrow= (duracao_media_exames_df.shape[0] +3)+(profissionais_necessarios_df.shape[0] +3)+(alocacao_df.shape[0] +3))
  output.seek(0)

  return output