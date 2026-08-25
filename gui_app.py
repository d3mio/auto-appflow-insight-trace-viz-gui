import tkinter as tk
from tkinter import ttk, Canvas, Frame, Label, Scrollbar, messagebox
import random
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

class AppFlowInsight:
    def __init__(self, root):
        self.root = root
        self.root.title('AppFlow Insight - Distributed Trace Visualizer')
        self.root.geometry('1200x800')
        self.root.configure(bg='#2d2d2d')
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background='#2d2d2d', foreground='white')
        self.style.configure('TFrame', background='#2d2d2d')
        self.style.configure('TLabel', background='#2d2d2d', foreground='white')
        self.style.configure('TButton', background='#3d3d3d', foreground='white', bordercolor='#3d3d3d')
        self.style.map('TButton', background=[('active', '#4d4d4d')])
        
        self.traces = []
        self.anomalies = []
        self.heatmap_data = defaultdict(list)
        
        self.create_main_panel()
        self.start_demo_data_thread()
    
    def create_main_panel(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls and trace list
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        control_frame = ttk.LabelFrame(left_panel, text='Controls', width=280)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text='Start Monitoring', command=self.start_monitoring).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text='Stop Monitoring', command=self.stop_monitoring).pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(control_frame, text='Analyze Anomalies', command=self.analyze_anomalies).pack(fill=tk.X, padx=5, pady=5)
        
        # Time range selector
        time_frame = ttk.LabelFrame(left_panel, text='Time Range', width=280)
        time_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.time_var = tk.StringVar(value='5m')
        for t in ['5m', '15m', '30m', '1h', '4h']:
            ttk.Radiobutton(time_frame, text=t, variable=self.time_var, value=t).pack(anchor=tk.W, padx=5)
        
        # Services filter
        filter_frame = ttk.LabelFrame(left_panel, text='Service Filter', width=280)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.services = ['auth', 'payment', 'inventory', 'shipping', 'gateway']
        self.service_vars = {}
        for service in self.services:
            self.service_vars[service] = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(filter_frame, text=service, variable=self.service_vars[service], 
                                  command=self.update_display)
            cb.pack(anchor=tk.W, padx=5)
        
        # Trace list
        trace_frame = ttk.LabelFrame(left_panel, text='Recent Traces', width=280)
        trace_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.trace_list = tk.Listbox(trace_frame, bg='#3d3d3d', fg='white', selectbackground='#4d4d4d')
        self.trace_list.pack(fill=tk.BOTH, expand=True)
        self.trace_list.bind('<<ListboxSelect>>', self.on_trace_select)
        
        # Right panel - Visualizations
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Trace visualization canvas
        trace_viz_frame = ttk.LabelFrame(right_panel, text='Trace Visualization')
        trace_viz_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = Canvas(trace_viz_frame, bg='#3d3d3d', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Metrics frame
        metrics_frame = ttk.Frame(right_panel)
        metrics_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Latency heatmap
        heatmap_frame = ttk.LabelFrame(metrics_frame, text='Latency Heatmap')
        heatmap_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.set_title('Service Latency', pad=10)
        self.heatmap_plot = ax.imshow([[0]*5], cmap='RdYlGn_r', aspect='auto')
        plt.colorbar(self.heatmap_plot, ax=ax)
        ax.set_xticks(range(5))
        ax.set_xticklabels(self.services)
        ax.set_yticks([0])
        ax.set_yticklabels(['Latency (ms)'])
        
        self.canvas_heatmap = FigureCanvasTkAgg(fig, master=heatmap_frame)
        self.canvas_heatmap.draw()
        self.canvas_heatmap.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Status indicators
        status_frame = ttk.LabelFrame(right_panel, text='System Status')
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_vars = {
            'Running Services': tk.StringVar(value='5/5 Normal'),
            'Avg Latency': tk.StringVar(value='45ms'),
            'Error Rate': tk.StringVar(value='0.2%'),
            'Anomalies': tk.StringVar(value='2 Detected')
        }
        
        for i, (name, var) in enumerate(self.status_vars.items()):
            f = ttk.Frame(status_frame)
            f.grid(row=0, column=i, padx=10, pady=5, sticky='ew')
            ttk.Label(f, text=name).pack()
            ttk.Label(f, textvariable=var, font=('Helvetica', 10, 'bold')).pack()
        
        # Status light indicator
        self.status_light = Canvas(status_frame, width=20, height=20, bg='green', highlightthickness=0)
        self.status_light.grid(row=0, column=4, padx=10, pady=5)
    
    def start_monitoring(self):
        self.status_light.config(bg='green')
        messagebox.showinfo('Monitoring', 'Started monitoring application traces')
    
    def stop_monitoring(self):
        self.status_light.config(bg='red')
        messagebox.showinfo('Monitoring', 'Stopped monitoring application traces')
    
    def analyze_anomalies(self):
        self.anomalies = [random.choice(self.traces) for _ in range(2)] if len(self.traces) > 0 else []
        self.status_vars['Anomalies'].set(f'{len(self.anomalies)} Detected')
        messagebox.showinfo('Anomalies', f'Found {len(self.anomalies)} performance anomalies')
    
    def update_display(self):
        filtered_traces = [t for t in self.traces if self.service_vars[t['root_service']].get()]
        self.trace_list.delete(0, tk.END)
        for trace in filtered_traces[-20:]:
            self.trace_list.insert(tk.END, f"{trace['root_service']} - {trace['duration']}ms")
        
        self.update_heatmap()
        self.draw_trace_diagram()
    
    def update_heatmap(self):
        if not self.traces:
            return
        
        heatmap_values = []
        for service in self.services:
            latencies = [t['span_details'].get(service, {}).get('latency', 0) 
                         for t in self.traces[-50:] if service in t['span_details']]
            avg_latency = sum(latencies)/len(latencies) if latencies else 0
            heatmap_values.append(avg_latency)
        
        # Update heatmap data
        self.heatmap_plot.set_data([heatmap_values])
        self.heatmap_plot.set_clim(vmin=0, vmax=max(heatmap_values) * 1.2 if heatmap_values else 100)
        self.canvas_heatmap.draw()
        
        # Update status
        avg_lat = sum(heatmap_values)/len(heatmap_values) if heatmap_values else 0
        self.status_vars['Avg Latency'].set(f'{int(avg_lat)}ms')
    
    def draw_trace_diagram(self):
        self.canvas.delete('all')
        
        if not self.trace_list.curselection():
            return
        
        selected_idx = self.trace_list.curselection()[0]
        trace = self.traces[selected_idx] if selected_idx < len(self.traces) else None
        
        if not trace:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Draw timeline
        max_duration = trace['duration']
        self.canvas.create_line(50, 50, canvas_width-50, 50, fill='#555555')
        
        # Draw services
        y_pos = 80
        service_positions = {}
        for i, service in enumerate(trace['path']):
            service_positions[service] = y_pos
            self.canvas.create_text(30, y_pos, text=service, fill='white', anchor=tk.E)
            self.canvas.create_rectangle(50, y_pos-15, 50 + (max_duration/2 if max_duration > 0 else 10), y_pos+15, 
                                         fill='#4d4d4d', outline='#555555')
            self.canvas.create_text(50 + (max_duration/2), y_pos, text=f"{trace['span_details'][service]['latency']}ms", 
                                     fill='white')
            y_pos += 50
        
        # Draw connections
        for i in range(len(trace['path'])-1):
            start = trace['path'][i]
            end = trace['path'][i+1]
            
            start_x = 50 + (trace['span_details'][start]['duration']/max_duration) * (canvas_width-100)
            start_y = service_positions[start]
            end_x = 50
            end_y = service_positions[end]
            
            self.canvas.create_line(start_x, start_y, end_x, end_y, fill='#777777', dash=(3,2))
    
    def on_trace_select(self, event):
        self.draw_trace_diagram()
    
    def generate_demo_trace(self):
        services_pool = self.services.copy()
        root_service = random.choice(services_pool)
        path = sorted(
            random.sample(services_pool, random.randint(2, len(services_pool))),
            key=lambda x: self.services.index(x)
        )
        
        if root_service not in path:
            path.insert(0, root_service)
        
        total_duration = random.randint(50, 500)
        spans = {}
        current_time = 0
        
        for service in path:
            if service == path[-1]:
                span_duration = total_duration - current_time
            else:
                span_duration = random.randint(10, min(200, total_duration - current_time))
            
            spans[service] = {
                'latency': span_duration,
                'duration': span_duration,
                'timestamp': current_time
            }
            current_time += span_duration
        
        trace = {
            'trace_id': f"demo-{time.time()}",
            'root_service': root_service,
            'path': path,
            'duration': total_duration,
            'span_details': spans,
            'timestamp': time.time()
        }
        
        return trace
    
    def start_demo_data_thread(self):
        def demo_data_worker():
            while True:
                trace = self.generate_demo_trace()
                self.traces.append(trace)
                self.update_display()
                time.sleep(random.uniform(0.5, 2))
        
        thread = threading.Thread(target=demo_data_worker, daemon=True)
        thread.start()

if __name__ == '__main__':
    root = tk.Tk()
    app = AppFlowInsight(root)
    root.mainloop()