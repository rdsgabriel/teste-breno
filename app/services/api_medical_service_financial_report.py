import os
import time
import json
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from json import JSONDecodeError
import orjson

load_dotenv()

# — CONFIGURAÇÃO DA API —
API_URL       ='https://api.grupobrmed.com.br/api/reports/medical-service-financial-report/'
SERVICE_TOKEN = os.getenv("SERVICE_TOKEN")
USERNAME      = os.getenv("USERNAME")


def get_report(session: requests.Session, params: dict):
    print(f"[get_report] iniciando chamada para: {params!r}")
    headers = {
        "Service-Token": SERVICE_TOKEN,
        "Client-Name":   USERNAME,
    }
    parametros ={"service_date":params,
                 "service_location": "Rede Própria"
                 }
    try:
        resp = session.get(API_URL, params=parametros, headers=headers)
        resp.raise_for_status()
    except RequestException as e:
        print(f"[get_report] Erro HTTP para {params!r}: {e}")
        return []

    if not resp.text:
        print(f"[get_report] sem conteúdo para: {params!r}")
        return []

    try:
        data = orjson.loads(resp.content)
    except (ValueError, JSONDecodeError):
        print(f"[get_report] JSON inválido para: {params!r}")
        return []

    #print(f"[get_report] concluído com sucesso para: {params!r}")
    return data


def bucket_calls_sync(params_list, max_workers=10):
    # Início da medição de tempo
    t_start = time.perf_counter()

    # Cria Session com pool do mesmo tamanho do executor
    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=max_workers, pool_maxsize=max_workers)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {}
        for p in params_list:
            #print(f"[bucket_calls] agendando chamada para: {p!r}")
            futuros[executor.submit(get_report, session, p)] = p

        for futuro in as_completed(futuros):
            param = futuros[futuro]
            try:
                report = futuro.result()
                if report:
                    yield report # Usa yield em vez de results.append()
                # se report == [], já foi logado dentro de get_report
            except Exception as e:
                print(f"[bucket_calls] exceção ao processar {param!r}: {e}")

    # Fim da medição de tempo
    t_end = time.perf_counter()
    print(f"[bucket_calls] duração total: {(t_end - t_start):.2f} segundos")

    session.close()


    # with open(JSON_FILE, "w", encoding="utf-8") as f:
    #     json.dump(json_report, f/, ensure_ascii=False, indent=2)