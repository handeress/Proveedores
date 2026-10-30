#!/usr/bin/env python3
"""Deja una carga cifrada en el buzón de la app Proveedores.

Uso:  PROVEEDORES_CLAVE='...' python3 herramientas/buzon.py carga.json "Descripción corta"

carga.json: {"app":"proveedores","v":1,"data":{contactos,materiales,cotizaciones,fotos,proyectos,lista}}
Mismo formato del respaldo. La app la SUMA (no borra) y no duplica si se repite (usa los id).
Luego: git add buzon && git commit && git push. La app la toma al abrir con internet.
Cifrado igual que carga.bin: salt(16) + iv(12) + AES-256-GCM, clave por PBKDF2-SHA256 200000 iteraciones.
"""
import json, os, sys, datetime, re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def main():
    if len(sys.argv) < 3: sys.exit(__doc__)
    clave = os.environ.get('PROVEEDORES_CLAVE', '').strip()
    if not clave: sys.exit('Falta PROVEEDORES_CLAVE')
    o = json.load(open(sys.argv[1], encoding='utf-8'))
    if o.get('app') != 'proveedores' or 'data' not in o: sys.exit('El JSON no tiene el formato de la app')
    raiz = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'buzon')
    os.makedirs(raiz, exist_ok=True)
    ahora = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5)))
    slug = re.sub(r'[^a-z0-9]+', '-', sys.argv[2].lower())[:40].strip('-')
    cid = ahora.strftime('%Y%m%d-%H%M%S') + '-' + slug
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200000).derive(clave.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(o, ensure_ascii=False).encode('utf-8'), None)
    open(os.path.join(raiz, cid + '.bin'), 'wb').write(salt + iv + ct)
    ip = os.path.join(raiz, 'indice.json')
    ind = json.load(open(ip, encoding='utf-8')) if os.path.exists(ip) else {'cargas': []}
    ind['cargas'].append({'id': cid, 'fecha': ahora.isoformat(timespec='seconds'), 'desc': sys.argv[2], 'archivo': cid + '.bin'})
    json.dump(ind, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Carga lista:', cid)

if __name__ == '__main__': main()
