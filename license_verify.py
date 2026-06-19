import hashlib, hmac, struct, time, os, sys
_SECRET_SEED = b'FileOrg2026Secret!@#$%'
_SECRET_SALT = b'FileOrgSalt2026_###'
_HMAC_SALT_1 = hashlib.sha256(b'enc_v2_st' + _SECRET_SEED).digest()[:16]
_HMAC_SALT_2 = hashlib.sha256(b'auth_v2_st' + _SECRET_SEED).digest()[:16]
CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'; _B32_REV = {c: i for i, c in enumerate(CROCKFORD)}
def _derive_keys():
    m = hashlib.pbkdf2_hmac('sha256', _SECRET_SEED, _SECRET_SALT, 200_000, dklen=64)
    return hmac.new(m[:32], _HMAC_SALT_1, 'sha256').digest(), hmac.new(m[32:], _HMAC_SALT_2, 'sha256').digest()
def _hmac_ctr(d,k,n):
    r=bytearray()
    for i in range(0,len(d),32):
        c=struct.pack('>QQ',n,i//32); ks=hmac.new(k,c,'sha256').digest()
        for a,b in zip(d[i:i+32],ks): r.append(a^b)
    return bytes(r)
def _b32_decode(s):
    s=s.upper().replace('-','').replace(' ','').lstrip('\ufeff')
    if s.startswith('FOR1'[:3]): s=s[3:]
    if s and s[0].isdigit(): s=s[1:]
    bits=bit_len=0; result=[]
    for c in s:
        if c not in _B32_REV: raise ValueError(f'Invalid: {c}')
        bits=(bits<<5)|_B32_REV[c]; bit_len+=5
        while bit_len>=8: bit_len-=8; result.append((bits>>bit_len)&0xFF)
    return bytes(result)
def _customer_id(name): return struct.unpack('>H',hashlib.sha256(name.encode()).digest()[:2])[0]
def _find_license_file():
    if getattr(sys,'frozen',False):
        p=os.path.join(os.path.dirname(sys.executable),'license.key')
        if os.path.isfile(p): return p
    for d in [os.getcwd(),os.path.dirname(os.path.abspath(__file__))]:
        p=os.path.join(d,'license.key')
        if os.path.isfile(p): return p
    return None
def get_license_info():
    p=_find_license_file()
    if not p: return {'status':'no_license'}
    try:
        with open(p,'r',encoding='utf-8-sig') as f: c=f.read().strip()
    except: return {'status':'invalid'}
    if not c: return {'status':'invalid'}
    ls=c.split('\n'); ks,cs=ls[0].strip(),ls[1].strip() if len(ls)>1 else ''
    try: cb=_b32_decode(ks)
    except: return {'status':'invalid'}
    if len(cb)!=23: return {'status':'invalid'}
    nc,ct,sg=struct.unpack('>H',cb[:2])[0],cb[2:17],cb[17:23]
    _,ak=_derive_keys()
    if not hmac.compare_digest(sg,hmac.new(ak,b'\x01'+cb[:17],'sha256').digest()[:6]): return {'status':'invalid'}
    ek,_=_derive_keys(); pl=_hmac_ctr(ct,ek,nc)
    if len(pl)!=15: return {'status':'invalid'}
    v,ex,ci,_=struct.unpack('>BIH8s',pl)
    now=int(time.time()); es='Permanent' if ex>=0xFFFFFF00 else time.strftime('%Y-%m-%d',time.localtime(ex))
    rs=max(0,ex-now) if ex<0xFFFFFF00 else -1; rd=rs//86400 if rs>=0 else -1
    no=not cs or _customer_id(cs)==ci
    return {'status':'valid','expire_str':es,'customer':cs,'remaining_days':rd,'name_ok':no,'expired':rs==0 and rs>=0}
def check_license():
    i=get_license_info(); s=i.get('status','invalid')
    if s=='no_license': return False,'No license file'
    if s=='invalid': return False,'Invalid license'
    if i.get('remaining_days',0)>=0 and i.get('expired',False): return False,f'Expired ({i["expire_str"]})'
    if not i.get('name_ok',True): return False,'Name mismatch'
    return True,''
