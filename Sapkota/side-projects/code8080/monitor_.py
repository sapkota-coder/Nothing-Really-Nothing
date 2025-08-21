import tkinter as tk
import psutil
import GPUtil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style

# Dark background for plots
style.use('dark_background')

def get_cpu_usage():
    return psutil.cpu_percent()

def get_ram_usage():
    return psutil.virtual_memory().percent

def get_disk_usage():
    return psutil.disk_usage('/').percent

def get_gpu_info():
    try:
        gpu = GPUtil.getGPUs()[0]
        return gpu.load * 100, gpu.temperature
    except Exception:
        return None, None

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        for key in ['coretemp', 'cpu-thermal']:
            if key in temps:
                return temps[key][0].current
    except Exception:
        pass
    return None

def update_plots():
    cpu = get_cpu_usage()
    ram = get_ram_usage()
    disk = get_disk_usage()
    gpu_load, gpu_temp = get_gpu_info()
    cpu_temp = get_cpu_temp()

    axs[0, 0].cla()
    axs[0, 0].bar(["CPU"], [cpu], color='skyblue')
    axs[0, 0].set_ylim(0, 100)
    axs[0, 0].set_title(f"CPU Usage: {cpu:.1f}%", color='white')
    axs[0, 0].grid(True, color='gray', alpha=0.3)

    axs[0, 1].cla()
    axs[0, 1].bar(["RAM"], [ram], color='lime')
    axs[0, 1].set_ylim(0, 100)
    axs[0, 1].set_title(f"RAM Usage: {ram:.1f}%", color='white')
    axs[0, 1].grid(True, color='gray', alpha=0.3)

    axs[0, 2].cla()
    axs[0, 2].bar(["Disk"], [disk], color='orange')
    axs[0, 2].set_ylim(0, 100)
    axs[0, 2].set_title(f"Disk Usage: {disk:.1f}%", color='white')
    axs[0, 2].grid(True, color='gray', alpha=0.3)

    axs[1, 0].cla()
    if gpu_load is not None:
        axs[1, 0].bar(["GPU"], [gpu_load], color='red')
        axs[1, 0].set_ylim(0, 100)
        axs[1, 0].set_title(f"GPU Load: {gpu_load:.1f}%", color='white')
    else:
        axs[1, 0].bar(["GPU"], [0], color='gray')
        axs[1, 0].set_ylim(0, 100)
        axs[1, 0].set_title("GPU Load: Not Found", color='white')
    axs[1, 0].grid(True, color='gray', alpha=0.3)

    axs[1, 1].cla()
    if cpu_temp is not None:
        axs[1, 1].bar(["CPU Temp"], [cpu_temp], color='purple')
        axs[1, 1].set_ylim(20, 100)
        axs[1, 1].set_title(f"CPU Temp: {cpu_temp:.1f}°C", color='white')
    else:
        axs[1, 1].text(0.1, 0.5, "No CPU Temp Data", color='white')
    axs[1, 1].grid(True, color='gray', alpha=0.3)

    axs[1, 2].cla()
    if gpu_temp is not None:
        axs[1, 2].bar(["GPU Temp"], [gpu_temp], color='cyan')
        axs[1, 2].set_ylim(20, 100)
        axs[1, 2].set_title(f"GPU Temp: {gpu_temp:.1f}°C", color='white')
    else:
        axs[1, 2].bar(["GPU Temp"], [0], color='gray')
        axs[1, 2].set_ylim(0, 100)
        axs[1, 2].set_title("GPU Temp: Not Found", color='white')
    axs[1, 2].grid(True, color='gray', alpha=0.3)

    canvas.draw()
    root.after(1500, update_plots)  # Refresh every 1.5 seconds

def close_app(event=None):
    root.destroy()

# Setup GUI window
root = tk.Tk()
root.title("System Monitor - Dark Mode")
root.geometry("750x520")
root.configure(bg="#1e1e1e")
root.resizable(True, True)

# Create figure with 2 rows, 3 columns for subplots
fig, axs = plt.subplots(2, 3, figsize=(9, 6))
plt.tight_layout(pad=3.0)

# Embed plot into Tkinter canvas
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Bind keys to close app
root.bind('<Control-c>', close_app)
root.bind('<Control-C>', close_app)
root.bind('<Control-q>', close_app)
root.bind('<Control-Q>', close_app)
root.bind('<Escape>', close_app)  # Escape key also closes window

# Start updating plots
update_plots()

# Start the GUI loop
root.mainloop()
