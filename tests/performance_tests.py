#!/usr/bin/env python3
import timeit
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))
from crypto_utils import CryptoManager
from command_obfuscator import AIObfuscator
import time

def test_encryption_performance():
    master = os.urandom(32)
    salt = os.urandom(16)
    crypto = CryptoManager(master, salt)
    key = os.urandom(32)
    plaintext = b"A" * 1024
    aad = b"test"
    enc_time = timeit.timeit(lambda: crypto.encrypt_packet(key, plaintext, aad), number=1000)
    encrypted = crypto.encrypt_packet(key, plaintext, aad)
    dec_time = timeit.timeit(lambda: crypto.decrypt_packet(key, encrypted, aad), number=1000)
    print(f"Encrypt 1000x 1KB: {enc_time:.4f}s")
    print(f"Decrypt 1000x 1KB: {dec_time:.4f}s")
    return enc_time, dec_time

def test_obfuscation_performance():
    obf = AIObfuscator()
    cmd = "test command" * 10
    obf_time = timeit.timeit(lambda: obf.obfuscate_command(cmd), number=10000)
    obf_cmd = obf.obfuscate_command(cmd)
    deobf_time = timeit.timeit(lambda: obf.deobfuscate_command(obf_cmd), number=10000)
    print(f"Obfuscate 10000x: {obf_time:.4f}s")
    print(f"Deobfuscate 10000x: {deobf_time:.4f}s")
    return obf_time, deobf_time

def test_c2_channel_latency():
    # Simulate blockchain C2 latency
    import random
    latencies = []
    for _ in range(10):
        latencies.append(random.uniform(2, 10))  # seconds
    avg_latency = sum(latencies) / len(latencies)
    print(f"Blockchain C2 simulated latency: {avg_latency:.2f}s")
    return avg_latency

def test_p2p_discovery_time():
    import random
    times = []
    for _ in range(5):
        times.append(random.uniform(0.5, 3.0))
    avg = sum(times) / len(times)
    print(f"P2P peer discovery simulated time: {avg:.2f}s")
    return avg

if __name__ == "__main__":
    print("Performance Tests")
    print("=================")
    test_encryption_performance()
    test_obfuscation_performance()
    test_c2_channel_latency()
    test_p2p_discovery_time()