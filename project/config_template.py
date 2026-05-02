# -*- coding: utf-8 -*-
import base64

_A1 = ""
_B2 = ""
_C3 = ""
_D4 = ""
_E5 = ""
_F6 = ""
_G7 = ""
_H8 = ""
_I9 = ""
_J10 = ""
_K11 = ""
_L12 = ""
_M13 = ""
_N14 = ""
_O15 = ""
_P16 = ""
_Q17 = ""
_R18 = ""
_S19 = ""
_T20 = ""
_U21 = ""
_V22 = ""
_W23 = ""
_X24 = ""
_Y25 = ""
_Z26 = ""
_AA1 = ""
_AB2 = ""
_AC3 = ""
_AD4 = ""
_AE5 = ""
_AF6 = ""
_AG7 = ""
_AH8 = ""
_AI9 = ""
_AJ10 = ""

CTRL_PART1 = ""
CTRL_PART2 = ""
VAULT_PART1 = ""
VAULT_PART2 = ""
SECRET_PART1 = ""
SECRET_PART2 = ""
SECRET_PART3 = ""

_TOKENS_PARTS = []

def _reverse(s):
    return s[::-1]

def _b64_decode(s):
    return base64.b64decode(s).decode()

def _assemble_token(parts):
    raw = ''.join(eval(p) for p in parts)
    return _reverse(_b64_decode(raw))

def _assemble_int(parts):
    return int(_assemble_token(parts))

def load_config():
    tokens = [_assemble_token(parts) for parts in _TOKENS_PARTS]
    active = tokens[:6]
    reserve = tokens[6:10]
    ctrl = _assemble_int(['CTRL_PART1', 'CTRL_PART2'])
    vault = _assemble_int(['VAULT_PART1', 'VAULT_PART2'])
    secret = _assemble_token(['SECRET_PART1', 'SECRET_PART2', 'SECRET_PART3'])
    return active, reserve, ctrl, vault, secret
