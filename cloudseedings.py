# -*- coding: utf-8 -*-
"""
Created on Sun Nov 30 22:47:58 2025

@author: k
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
# import folium
import webbrowser


# ======================================
#   FUNÇÃO DE AVALIAÇÃO DA NUVEM
# ======================================

def evaluate_event(evt):
    cb = evt.get("cloud_base_m")
    ct = evt.get("cloud_top_m")
    ctmp = evt.get("cloud_top_temp_c")
    refl = evt.get("radar_reflectivity_dbz")
    prate = evt.get("precip_rate_mm_h", 0.0)
    rh = evt.get("rel_humidity_pct", 80)
    wind = evt.get("wind_speed_m_s", 5.0)
    lightning = evt.get("lightning", False)
    pw = evt.get("precipitable_water_mm", None)

    if lightning:
        return "NEGADO", "Atividade elétrica detectada."
    if prate > 20:
        return "NEGADO", "Precipitação muito alta (>20 mm/h)."
    if wind > 15:
        return "NEGADO", "Vento forte (>15 m/s)."
    if refl < 10:
        return "NEGADO", "Reflectividade muito baixa (<10 dBZ)."

    drone_ok = (cb is not None and ct is not None and 300 <= cb <= 2800 and ct <= 4000 and rh >= 60)
    aircraft_ok = (ct is not None and ctmp is not None and 3500 <= ct <= 9000 and ctmp <= -5 and rh >= 40)

    if drone_ok and aircraft_ok:
        return "APROVADO - MISTA", "Ambas plataformas adequadas."

    if drone_ok:
        return "APROVADO - DRONE", "Faixa ideal para drones."

    if aircraft_ok:
        return "APROVADO - AERONAVE", "Nuvem fria ideal para AgI."

    cond_msg = []

    if 10 <= prate <= 20:
        cond_msg.append("Precipitação moderada.")
    if 10 <= refl <= 15:
        cond_msg.append("Reflectividade marginal.")
    if pw is not None and pw < 10:
        cond_msg.append("Baixa coluna de água (PW).")

    if cond_msg:
        return "CONDICIONADO", " | ".join(cond_msg)

    return "NEGADO", "Parâmetros fora das faixas operacionais."


# ======================================
#     INTERFACE TKINTER
# ======================================

class CloudSeedingGUI:
    def __init__(self, root):
        self.root = root
        root.title("Cloud Seeding – Analisador + Mapa de Controle")
        root.geometry("820x700")

        self.fields = [
            ("Base da nuvem (m)", "cloud_base_m"),
            ("Topo da nuvem (m)", "cloud_top_m"),
            ("Temp topo (°C)", "cloud_top_temp_c"),
            ("Radar dBZ", "radar_reflectivity_dbz"),
            ("Precipitação (mm/h)", "precip_rate_mm_h"),
            ("Umidade (%)", "rel_humidity_pct"),
            ("Vento (m/s)", "wind_speed_m_s"),
            ("PW (mm)", "precipitable_water_mm"),
            ("Lightning 0/1", "lightning"),
            ("Latitude alvo", "lat"),
            ("Longitude alvo", "lon"),
        ]

        self.entries = {}

        title_label = tk.Label(root, text="Análise Meteorológica e Mapa de Controle",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        frame = tk.Frame(root)
        frame.pack()

        for i, (label, key) in enumerate(self.fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w")
            entry = ttk.Entry(frame, width=25)
            entry.grid(row=i, column=1)
            self.entries[key] = entry

        ttk.Button(root, text="Avaliar Nuvem", command=self.evaluate_single)\
            .pack(pady=10)

        ttk.Button(root, text="Gerar Mapa de Controle", command=self.generate_map)\
            .pack(pady=5)

        self.result_box = tk.Text(root, height=10, width=95)
        self.result_box.pack(pady=10)

        ttk.Button(root, text="Carregar CSV para avaliação em lote", command=self.load_csv)\
            .pack(pady=10)

    # ==================================================
    #       AVALIA UMA ÚNICA NUVEM
    # ==================================================
  
    def evaluate_single(self):
        try:
            evt = {}
            for label, key in self.fields:
                value = self.entries[key].get().strip()
                if key in ["lat", "lon"]:
                    evt[key] = float(value) if value else None
                elif key == "lightning":
                    evt[key] = bool(int(value)) if value else False
                else:
                    evt[key] = float(value) if value else None

            decision, reason = evaluate_event(evt)

            self.result_box.delete(1.0, tk.END)
            self.result_box.insert(tk.END, f"DECISÃO: {decision}\n")
            self.result_box.insert(tk.END, f"JUSTIFICATIVA: {reason}\n")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {e}")

    # ==================================================
    #       GERAR MAPA DE CONTROLE (FOLIUM)
    # ==================================================
  
    def generate_map(self):
        try:
            lat = float(self.entries["lat"].get())
            lon = float(self.entries["lon"].get())

            mapa = folium.Map(location=[lat, lon], zoom_start=11)

            # Marcador principal
            folium.Marker(
                [lat, lon],
                tooltip="Alvo da operação",
                icon=folium.Icon(color="blue", icon="cloud")
            ).add_to(mapa)

            # Área de risco (círculo vermelho)
            folium.Circle(
                location=[lat, lon],
                radius=3000,
                color="red",
                fill=True,
                fill_opacity=0.2,
                tooltip="Zona urbana sensível"
            ).add_to(mapa)

            # Área da bacia (círculo verde)
            folium.Circle(
                location=[lat + 0.02, lon - 0.02],
                radius=5000,
                color="green",
                fill=True,
                fill_opacity=0.15,
                tooltip="Bacia hídrica de recepção"
            ).add_to(mapa)

            # Base operacional do drone
            folium.Marker(
                [lat - 0.03, lon + 0.03],
                tooltip="Base Drone",
                icon=folium.Icon(color="darkpurple", icon="plane")
            ).add_to(mapa)

            save_path = "mapa_controle.html"
            mapa.save(save_path)
            webbrowser.open(save_path)

            messagebox.showinfo("Mapa pronto", "Mapa de controle gerado e aberto no navegador.")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar o mapa: {e}")

    # ==================================================
    #      AVALIAÇÃO EM LOTE (CSV)
    # ==================================================
  
    def load_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return

        df = pd.read_csv(path)
        outputs = []

        for _, row in df.iterrows():
            evt = {
                "cloud_base_m": row.get("cloud_base_m"),
                "cloud_top_m": row.get("cloud_top_m"),
                "cloud_top_temp_c": row.get("cloud_top_temp_c"),
                "radar_reflectivity_dbz": row.get("radar_reflectivity_dbz"),
                "precip_rate_mm_h": row.get("precip_rate_mm_h"),
                "rel_humidity_pct": row.get("rel_humidity_pct"),
                "wind_speed_m_s": row.get("wind_speed_m_s"),
                "precipitable_water_mm": row.get("precipitable_water_mm"),
                "lightning": bool(row.get("lightning", 0)),
            }
            decision, reason = evaluate_event(evt)
            row_out = row.to_dict()
            row_out["decision"] = decision
            row_out["reason"] = reason
            outputs.append(row_out)

        df_out = pd.DataFrame(outputs)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if save_path:
            df_out.to_csv(save_path, index=False)
            messagebox.showinfo("Sucesso", f"Relatório salvo em {save_path}")


# ==================================================
#              EXECUÇÃO DO PROGRAMA
# ==================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = CloudSeedingGUI(root)
    root.mainloop()
