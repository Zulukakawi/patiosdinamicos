# Genera datos/centros-rioja.json a partir del mapa oficial de centros del
# Gobierno de La Rioja (el GeoJSON que alimenta bi.larioja.org/pentaho/educacion/mapa_web).
#   py datos/generar-centros.py
# Fuente: https://www.larioja.org/educarioja-centros/es/buscador-centros/mapa-centros
import json, re, html, urllib.request, datetime, pathlib

URL = ('https://bi.larioja.org/pentaho/educacion/mapa_web/mapa.jsp?busqueda=&tipoCentro=todos'
       '&denomGen=todos&comarca=&municipio=&cra=todos&nivel=todos&etapa=todos&expediente=todos'
       '&matricula=todos&comedor=todos&transporte=todos&modalidad=todos&campania=%d'
       '&familia=todos&jornada=todos&tipo_exp=todos')
# Sin patio de recreo: no aportan nada al buscador de la app
EXCLUIR = {'E.O.I.', 'C.E.P.A.', 'C.E.M.', 'C.P.M.', 'E.S.D.'}

anio = datetime.date.today().year
raw = urllib.request.urlopen(URL % anio, timeout=60).read().decode('latin-1')  # el servidor sirve ISO-8859-1
datos = json.loads(raw)

def limpiar(t):
    return html.unescape(re.sub(r'\s+', ' ', t)).strip()

lista = []
for f in datos['features']:
    p = f['properties']
    sigla = p['tipoCentro']
    if sigla in EXCLUIR:
        continue
    lon, lat = f['geometry']['coordinates'][:2]
    parrafos = re.findall(r"<p[^>]*>(.*?)</p>", p['NOMBRE'], re.S)
    titulo = limpiar(re.sub(r'<[^>]+>', '', parrafos[0]))          # "I.E.S. - Valle del Cidacos"
    nombre = titulo.split(' - ', 1)[1] if ' - ' in titulo else titulo
    direccion = [limpiar(re.sub(r'<[^>]+>', '', x)) for x in parrafos[1].split('<br>')] if len(parrafos) > 1 else []
    municipio = direccion[1].split(' - ', 1)[1] if len(direccion) > 1 and ' - ' in direccion[1] else ''
    m = re.search(r'\*+\s*<br>(.*?)<br>', p['NOMBRE'])
    tipo = limpiar(re.sub(r'<[^>]+>', '', m.group(1))) if m else ''    # "Público - Instituto de Educación Secundaria"
    lista.append({
        'n': f"{sigla.replace('.', '')} {nombre}",   # "IES Valle del Cidacos"
        'm': municipio,
        'lat': round(lat, 6), 'lon': round(lon, 6),
        't': tipo.replace(' - ', ' · '),
        'd': direccion[0] if direccion else ''
    })

lista.sort(key=lambda c: (c['m'], c['n']))
salida = {
    'fuente': 'Gobierno de La Rioja — Mapa de centros (bi.larioja.org/pentaho/educacion/mapa_web)',
    'descargado': datetime.date.today().isoformat(),
    'lista': lista
}
destino = pathlib.Path(__file__).with_name('centros-rioja.json')
destino.write_text(json.dumps(salida, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'{len(lista)} centros -> {destino}')
