
import pandas as pd
import json
import gc # Importa o coletor de lixo

# === CONFIGURAÇÕES GERAIS ===
POSITION_JSON = "app/data/position_job.json"
HORAS_DE_FUNCIONAMENTO = 24
FATOR_OCUPACAO = 0.8  # 80% de eficiência operacional

FINANCIAL_JSON = "app/data/report.json"
DURATION_JSON = "app/data/report_time_medical.json"
CARGA_HORARIA_JSON = "app/data/workload_per_exam.json"

def tables_dinamic(report_medical_care,report_medical_care_times):
    try:
        # Processamento de report_medical_care (dados financeiros)
        # Constrói o DataFrame a partir do gerador
        df = pd.DataFrame(item for sublist in report_medical_care for item in sublist)
        gc.collect() # Força a coleta de lixo
        # 2) Verifica colunas necessárias
        required_columns = {"preco_venda", "data_atendimento", "filial_nome", "pedido_exame_id", "subexame_nome"}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise KeyError(f"As seguintes colunas estão faltando no DataFrame: {missing_columns}")

        # 3) Pré-processamento
        df["preco_venda"] = pd.to_numeric(df["preco_venda"], errors="coerce").fillna(0)

        # 4) Cálculos auxiliares
        dias_por_filial = df.groupby("filial_nome")["data_atendimento"].nunique()
        atend_por_filial = df.groupby("filial_nome")["pedido_exame_id"].nunique()

        # 5) Métrica 1: Soma do preço de venda
        pivot_preco_venda = df.pivot_table(
            index="data_atendimento",
            columns="filial_nome",
            values="preco_venda",
            aggfunc="sum",
            fill_value=0,
            margins=True,
            margins_name="Total Geral"
        )
        pivot_preco_venda.loc["Valor Médio(Dia)"] = pivot_preco_venda.loc["Total Geral"] / dias_por_filial
        pivot_preco_venda.loc["Ticket Médio"]     = pivot_preco_venda.loc["Total Geral"] / atend_por_filial
        pivot_preco_venda = pivot_preco_venda.round(2)

        # 6) Métrica 2: Número único de pacientes
        pivot_pacientes = df.pivot_table(
            index="data_atendimento",
            columns="filial_nome",
            values="pedido_exame_id",
            aggfunc="nunique",
            fill_value=0,
            margins=True,
            margins_name="Total Geral"
        )
        pivot_pacientes.loc["Média Atend./Dia"] = pivot_pacientes.loc["Total Geral"] / dias_por_filial
        pivot_pacientes = pivot_pacientes.round(2)

        # 7) Métrica 3: Contagem de subexames
        pivot_exames = df.pivot_table(
            index="data_atendimento",
            columns="filial_nome",
            values="subexame_nome",
            aggfunc="count",
            fill_value=0,
            margins=True,
            margins_name="Total Geral"
        )
        pivot_exames.loc["Média Atend./Dia"]      = pivot_exames.loc["Total Geral"] / dias_por_filial
        pivot_exames.loc["Exames por paciente"]   = pivot_exames.loc["Total Geral"] / atend_por_filial
        pivot_exames = pivot_exames.round(2)


        #------Relatório Produtividade-------

        # === CARREGAMENTO DE TEMPOS DE EXAMES ===
        # Processamento de report_medical_care_times (tempos de exames)
        df_tempos_exames = pd.DataFrame(item for sublist in report_medical_care_times for item in sublist)
        gc.collect()

                # === CARREGAMENTO DE POSIÇÕES DE TRABALHO ===
        with open(CARGA_HORARIA_JSON, 'r', encoding='utf-8') as f:
            carga_horaria_por_especialidade = {item['Rótulos de Linha']: item for item in json.load(f)}

        # === CARREGAMENTO DE POSIÇÕES DE TRABALHO ===
        with open(POSITION_JSON, 'r', encoding='utf-8') as f:
            mapeamento_posicoes = {item['Rótulos de Linha']: item for item in json.load(f)}


        # === TRANSFORMAÇÃO DE TEMPOS DE EXAMES PARA FORMATO LONGO ===
        colunas_duracao = [col for col in df_tempos_exames.columns if 'duracao' in col.lower()]
        df_duracoes = df_tempos_exames.melt(
            id_vars=['filial'],
            value_vars=colunas_duracao,
            var_name='exame_codigo',
            value_name='duracao_str'
        )
        df_duracoes = df_duracoes[
            df_duracoes['duracao_str'].notna() & (df_duracoes['duracao_str'].str.strip() != '')
        ] 

        df_duracoes['duracao_segundos'] = pd.to_timedelta(df_duracoes['duracao_str']).dt.total_seconds()
        df_duracoes['duracao_minutos'] = df_duracoes['duracao_segundos'].div(60).round(2)
        # === MAPEAMENTO DE AGRUPAMENTOS DE EXAMES POR ÁREA ===
        mapeamento_exames = {
            'ASSISTENCIAL_duracao': "EXAMES CLINICOS",
            'CARDIOLOGIA_duracao': "EXAMES COMPLEMENTARES",
            'CLIN_duracao': "EXAMES CLINICOS",
            'EEG_duracao': "EXAMES COMPLEMENTARES",
            'ENFBAS_duracao': "EXAMES COMPLEMENTARES",
            'ENF_duracao': "EXAMES COMPLEMENTARES",
            'FONO_duracao': "FONOAUDIOLOGIA",
            'HOMOLOG_duracao': "EXAMES CLINICOS",
            'LAB_duracao': "EXAMES COMPLEMENTARES",
            'LEITURA_TESTE_RAPIDO_ANTIGENO_duracao': "EXAMES COMPLEMENTARES",
            'LEITURA_TESTE_RAPIDO_IGG_IGM_duracao': "EXAMES COMPLEMENTARES",
            'ODONTO_duracao': "ODONTOLOGIA",
            'PISC_duracao': "PSICOLOGIA",
            'PREVIDENCIARIO_duracao': "EXAMES CLINICOS",
            'PRÉ_CLIN_duracao': "EXAMES CLINICOS",
            'RADIO_duracao': "RADIOLOGIA",
            'REALIZACAO_TESTE_RAPIDO_ANTIGENO_duracao': "EXAMES COMPLEMENTARES",
            'REALIZACAO_TESTE_RAPIDO_IGG_IGM_duracao': "EXAMES COMPLEMENTARES",
            'TESTE_ESFORCO_duracao':"EXAMES COMPLEMENTARES",
        }
        df_duracoes['exame'] = df_duracoes['exame_codigo'].map(mapeamento_exames).fillna(df_duracoes['exame_codigo'])
        df_duracoes['dias_uteis'] = df_duracoes['filial'].map(dias_por_filial)
        
        df_duracoes.loc[df_duracoes['exame'] == 'PSICOLOGIA','duracao_minutos'] /= 2
        # Média de minutos por exame e filial
        df_duracoes['media_minutos'] = (
            df_duracoes.groupby(['filial', 'exame'])['duracao_minutos']
            .transform('mean')
        ).round(2)

        # === TABELA PIVÔ COM MÉDIA DE DURAÇÃO ===
        tabela_duracao_media = df_duracoes.pivot_table(
            index='exame',
            columns='filial',
            values='media_minutos',
            aggfunc='sum',
            fill_value=0, 
            margins=True,
            margins_name="Total Geral"
        ).round(2)

        df_necessidade_pessoal = df_duracoes.groupby(['filial', 'exame', 'dias_uteis'])['media_minutos'].sum().reset_index()
        #soma de médias
        df_necessidade_pessoal['sum_media_minutos'] = (
            df_necessidade_pessoal.groupby(['filial'])['media_minutos']
            .transform('sum')
        ).round(2)

        # === CÁLCULO DE CARGA HORARIA POR ESPECIALIDADE ===
        def buscar_carga_horaria(row):
            return carga_horaria_por_especialidade.get(row['exame'], {}).get(row['filial'])
        df_necessidade_pessoal['carga_horaria'] = df_necessidade_pessoal.apply(buscar_carga_horaria, axis=1)

        # === CÁLCULO DE ALOCAÇÂO DE PROFISSIONAIS POR EXAME ===
        df_necessidade_pessoal['profissionais_necessarios'] = (
            ((df_necessidade_pessoal['media_minutos'] / df_necessidade_pessoal['dias_uteis'])
             / (df_necessidade_pessoal['carga_horaria']*60))  / FATOR_OCUPACAO + 0.49
        ).round(0)


        # === CÁLCULO DE POSIÇÕES DE TRABALHO EXISTENTES ===
        def buscar_posicao(row):
            return mapeamento_posicoes.get(row['exame'], {}).get(row['filial'])


        df_necessidade_pessoal['posicoes_existentes'] = df_necessidade_pessoal.apply(buscar_posicao, axis=1)

        # === CÁLCULO DE ALOCAÇÃO POR EXAME ===
        df_necessidade_pessoal['alocacao'] = df_necessidade_pessoal.apply(
            lambda row: row['profissionais_necessarios'] / row['posicoes_existentes']
            if row['posicoes_existentes'] else None,
            axis=1
        )

        # === PIVÔ: TOTAL DE PROFISSIONAIS NECESSÁRIOS POR EXAME E FILIAL ===
        tabela_profissionais_necessarios = df_necessidade_pessoal.pivot_table(
            index='exame',
            columns='filial',
            values='profissionais_necessarios',
            aggfunc='sum',
            fill_value=0,
            margins=True,
            margins_name="Total Geral"
        )

        # === PIVÔ: ALOCAÇÃO POR EXAME E FILIAL ===
        tabela_alocacao = df_necessidade_pessoal.pivot_table(
            index='exame',
            columns='filial',
            values='alocacao',
            aggfunc='sum',
            fill_value=0
        ).rename_axis("%Alocação").round(2)

        # === CÁLCULO DE ALOCAÇÃO GERAL POR FILIAL ===
        df_alocacao_total_por_filial = df_necessidade_pessoal.groupby('filial')['profissionais_necessarios'].sum().reset_index()
        mapeamento_corpo_tecnico = mapeamento_posicoes.get("Corpo Técnico", {})
        df_alocacao_total_por_filial["corpo_tecnico"] = df_alocacao_total_por_filial["filial"].map(mapeamento_corpo_tecnico)

        # Cálculo de alocação total por filial (profissionais necessários / corpo técnico disponível)
        df_alocacao_total_por_filial['alocacao_total'] = (
            df_alocacao_total_por_filial["profissionais_necessarios"] /
            df_alocacao_total_por_filial["corpo_tecnico"]
        )

        # === AJUSTES FINAIS DE FORMATAÇÃO  ALOCAÇÃO ===
        tabela_alocacao.columns = tabela_alocacao.columns.str.strip()
        df_alocacao_total_por_filial["filial"] = df_alocacao_total_por_filial["filial"].str.strip()

        # === INSERE ALOCAÇÃO TOTAL COMO LINHA FINAL NO PIVÔ DE ALOCAÇÃO ===
        linha_total_alocacao = (
            df_alocacao_total_por_filial.set_index("filial")["alocacao_total"]
            .reindex(tabela_alocacao.columns)
        )
        tabela_alocacao.loc["Total Geral"] = linha_total_alocacao

        # === CÁLCULO DE OCUPAÇÃO POR EXAME ===

        df_necessidade_pessoal['ocupacao'] =( 
            (
                df_necessidade_pessoal['media_minutos'] /
                (
                    df_necessidade_pessoal['posicoes_existentes'] *
                    (df_necessidade_pessoal['carga_horaria'] * 60)*
                    df_necessidade_pessoal['dias_uteis']
                ) 
            )/ FATOR_OCUPACAO
        )
        

        # === PIVÔ: ALOCAÇÃO POR EXAME E FILIAL ===
        tabela_ocupacao = df_necessidade_pessoal.pivot_table(
            index='exame',
            columns='filial',
            values='ocupacao',
            aggfunc='sum',
            fill_value=0
        ).rename_axis("%Ocupação").round(2)

        df_necessidade_pessoal['media_minutos_ocupacao'] = (
            df_necessidade_pessoal['media_minutos']*df_necessidade_pessoal['ocupacao']
            )
        df_ocupacao_total_por_filial = (
        df_necessidade_pessoal.groupby(['filial',"sum_media_minutos"])['media_minutos_ocupacao'].sum().reset_index()
        )
        df_ocupacao_total_por_filial['ocupacao_total']=(
            df_ocupacao_total_por_filial['media_minutos_ocupacao']/df_ocupacao_total_por_filial['sum_media_minutos']
            )
        # === AJUSTES FINAIS DE FORMATAÇÃO  ALOCAÇÃO ===
        tabela_ocupacao.columns = tabela_ocupacao.columns.str.strip()
        df_ocupacao_total_por_filial["filial"] = df_ocupacao_total_por_filial["filial"].str.strip()

        # === INSERE ALOCAÇÃO TOTAL COMO LINHA FINAL NO PIVÔ DE ALOCAÇÃO ===
        linha_total_ocupacao = (
            df_ocupacao_total_por_filial.set_index("filial")["ocupacao_total"]
            .reindex(tabela_ocupacao.columns)
        )
        tabela_ocupacao.loc["Total Geral"] = linha_total_ocupacao

        # === SAÍDAS FINAIS ===
        # print(tabela_duracao_media)                    # Tabela detalhada por exame
        # print(tabela_profissionais_necessarios)          # Pivot com profissionais necessários
        # print(tabela_alocacao)                           # Pivot com alocação por exame %
        #print(tabela_ocupacao.round(2))

        return df, pivot_preco_venda, pivot_pacientes, pivot_exames,tabela_duracao_media,tabela_profissionais_necessarios,tabela_alocacao, tabela_ocupacao

    except Exception as e:
        raise RuntimeError(f"Erro ao gerar as tabelas dinâmicas: {e}")


# if __name__ == "__main__":
#     tables_dinamic(None,None)