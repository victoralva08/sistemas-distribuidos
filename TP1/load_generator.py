#!/usr/bin/env python3
"""
load_generator.py
-----------------
Ferramenta para stress testing da API de pedidos.

Envia múltiplas requisições concorrentes para a API REST.

Uso:
    python3 load_generator.py --target http://localhost:5000/api/order \
                              --total 5000 \
                              --concurrency 10 \
                              --interval 0.1

Exemplos:
    # Teste rápido (100 pedidos)
    python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order --total 100

    # Teste médio (5000 pedidos, 10 concurrent)
    python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order --total 5000 --concurrency 10

    # Teste de carga sustentada (10k com delay entre requisições)
    python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order --total 10000 --interval 0.05
"""

import requests
import concurrent.futures
import time
import argparse
import random
import sys
from datetime import datetime

PRODUCTS = ["notebook", "smartphone", "tablet", "monitor", "headset", "keyboard", "mouse"]

class LoadGenerator:
    def __init__(self, api_url, total=1000, concurrency=5, interval=0):
        self.api_url = api_url
        self.total = total
        self.concurrency = concurrency
        self.interval = interval
        
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.latencies = []
    
    def generate_order(self):
        """Gera um pedido aleatório."""
        return {
            "customer_id": f"CUST-{random.randint(1, 10000):05d}",
            "product_id": random.choice(PRODUCTS),
            "quantity": random.randint(1, 5),
            "amount": round(random.uniform(100, 5000), 2)
        }
    
    def submit_order(self, order_num):
        """Submete um pedido à API."""
        order = self.generate_order()
        
        if self.interval > 0:
            time.sleep(self.interval)
        
        try:
            start = time.time()
            response = requests.post(
                self.api_url,
                json=order,
                timeout=10
            )
            latency = time.time() - start
            self.latencies.append(latency)
            
            if response.status_code == 201:
                self.success_count += 1
                return (True, latency, None)
            else:
                self.error_count += 1
                return (False, latency, f"HTTP {response.status_code}")
        
        except requests.exceptions.Timeout:
            self.error_count += 1
            return (False, None, "Timeout")
        except requests.exceptions.ConnectionError as e:
            self.error_count += 1
            return (False, None, f"Connection Error: {str(e)}")
        except Exception as e:
            self.error_count += 1
            return (False, None, str(e))
    
    def run(self):
        """Executa o teste de carga."""
        print("\n" + "="*70)
        print("  STRESS TEST - Producer API")
        print("="*70)
        print(f"Target:      {self.api_url}")
        print(f"Total Req:   {self.total:,}")
        print(f"Concurrency: {self.concurrency}")
        print(f"Interval:    {self.interval}s")
        print("="*70 + "\n")
        
        self.start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [
                executor.submit(self.submit_order, i)
                for i in range(1, self.total + 1)
            ]
            
            # Progress tracking
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                success, latency, error = future.result()
                
                if error:
                    self.errors.append(error)
                
                # Print progress every 10% or every 100 requests
                if completed % max(self.total // 10, 100) == 0:
                    progress = (completed / self.total) * 100
                    elapsed = time.time() - self.start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    eta = (self.total - completed) / rate if rate > 0 else 0
                    print(f"  [{progress:>5.1f}%] {completed:>6,}/{self.total:,} | "
                          f"Rate: {rate:>7.1f} req/s | ETA: {eta:>6.1f}s")
        
        self.end_time = time.time()
        self.print_summary()
    
    def print_summary(self):
        """Exibe sumário dos resultados."""
        elapsed = self.end_time - self.start_time
        total_requests = self.success_count + self.error_count
        success_rate = (self.success_count / total_requests * 100) if total_requests > 0 else 0
        throughput = total_requests / elapsed if elapsed > 0 else 0
        
        print("\n" + "="*70)
        print("  RESULTADOS")
        print("="*70)
        print(f"Total Requests:  {total_requests:,}")
        print(f"Successes:       {self.success_count:,} ({success_rate:.1f}%)")
        print(f"Errors:          {self.error_count:,}")
        print(f"Total Time:      {elapsed:.2f}s")
        print(f"Throughput:      {throughput:.2f} req/s")
        
        if self.latencies:
            latencies_sorted = sorted(self.latencies)
            print(f"\nLatency Stats:")
            print(f"  Min:     {min(self.latencies)*1000:.2f}ms")
            print(f"  Max:     {max(self.latencies)*1000:.2f}ms")
            print(f"  Mean:    {sum(self.latencies)/len(self.latencies)*1000:.2f}ms")
            print(f"  Median:  {latencies_sorted[len(latencies_sorted)//2]*1000:.2f}ms")
            print(f"  P95:     {latencies_sorted[int(len(latencies_sorted)*0.95)]*1000:.2f}ms")
            print(f"  P99:     {latencies_sorted[int(len(latencies_sorted)*0.99)]*1000:.2f}ms")
        
        if self.errors:
            print(f"\nTop Errors:")
            from collections import Counter
            error_counts = Counter(self.errors)
            for error, count in error_counts.most_common(5):
                print(f"  {error}: {count}")
        
        print("="*70 + "\n")
        
        return success_rate == 100.0  # Overall success


def main():
    parser = argparse.ArgumentParser(
        description="Stress test para API de pedidos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python3 load_generator.py --target http://localhost:5000/api/order --total 100
  python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order --total 5000 --concurrency 10
  python3 load_generator.py --target http://ORACLE_VM_IP:5000/api/order --total 10000 --interval 0.05
        """
    )
    
    parser.add_argument("--target", required=True, help="URL da API (ex: http://localhost:5000/api/order)")
    parser.add_argument("--total", type=int, default=1000, help="Total de requisições (default: 1000)")
    parser.add_argument("--concurrency", type=int, default=5, help="Threads concorrentes (default: 5)")
    parser.add_argument("--interval", type=float, default=0, help="Delay entre requisições em segundos (default: 0)")
    
    args = parser.parse_args()
    
    gen = LoadGenerator(
        api_url=args.target,
        total=args.total,
        concurrency=args.concurrency,
        interval=args.interval
    )
    
    try:
        gen.run()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Cancelado pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
