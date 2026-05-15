import re
import sys
import os
import matplotlib.pyplot as plt

# ==========================================
# Style Configuration
# ==========================================
plt.rcParams.update({
    "text.usetex": False,                 
    "font.family": "serif",               
    "mathtext.fontset": "cm",             
    "axes.titlesize": 20,                 # Tăng cỡ chữ tiêu đề
    "axes.labelsize": 16,                 # Tăng cỡ chữ nhãn trục (chữ "Time Slot")
    "xtick.labelsize": 10,                # GIỮ NGUYÊN cỡ chữ số trên trục X (10)
    "ytick.labelsize": 14,                # Tăng cỡ chữ tên CPU trục Y
    "legend.fontsize": 14,                
})

def parse_input(input_filename):
    """
    Đọc file input để lấy cấu hình hệ thống.
    """
    num_cpus = 1
    try:
        with open(input_filename, 'r') as f:
            first_line = f.readline().strip()
            if first_line:
                parts = first_line.split()
                if len(parts) >= 2:
                    num_cpus = int(parts[1])
    except Exception as e:
        print(f"Lỗi đọc file input: {e}")
    return num_cpus

def parse_log(filename, num_cpus):
    """
    Đọc file log và xây dựng lịch chạy cho mỗi CPU.
    """
    cpu_state: dict[int, int | None] = {i: None for i in range(num_cpus)}
    cpu_schedule: dict[int, dict[int, int | None]] = {i: {} for i in range(num_cpus)}
    current_time = None

    time_slot_pattern = re.compile(r"Time slot\s+(\d+)")
    dispatched_pattern = re.compile(r"CPU\s+(\d+):\s+Dispatched process\s+(\d+)")
    processed_pattern = re.compile(r"CPU\s+(\d+):\s+Processed\s+(\d+)\s+has finished")
    stopped_pattern = re.compile(r"CPU\s+(\d+)\s+stopped")

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            ts_match = time_slot_pattern.search(line)
            if ts_match:
                current_time = int(ts_match.group(1))
                for cpu in cpu_state:
                    cpu_schedule[cpu][current_time] = cpu_state[cpu]
                continue
            
            d_match = dispatched_pattern.search(line)
            if d_match:
                cpu = int(d_match.group(1))
                proc = int(d_match.group(2))
                if cpu in cpu_state:
                    cpu_state[cpu] = proc
                    if current_time is not None:
                        cpu_schedule[cpu][current_time] = proc
                continue
            
            p_match = processed_pattern.search(line)
            if p_match:
                cpu = int(p_match.group(1))
                if cpu in cpu_state:
                    cpu_state[cpu] = None
                    if current_time is not None:
                        cpu_schedule[cpu][current_time] = None
                continue
            
            s_match = stopped_pattern.search(line)
            if s_match:
                cpu = int(s_match.group(1))
                if cpu in cpu_state:
                    cpu_state[cpu] = None
                    if current_time is not None:
                        cpu_schedule[cpu][current_time] = None
                continue
                
    return cpu_schedule

def merge_schedule(schedule):
    """
    Gom các time slot liên tiếp.
    """
    intervals = []
    sorted_times = sorted(schedule.keys())
    if not sorted_times:
        return intervals
    
    current_proc = schedule[sorted_times[0]]
    start_time = sorted_times[0]
    
    for t in sorted_times[1:]:
        if schedule[t] == current_proc:
            continue
        else:
            duration = t - start_time
            if duration > 0:
                intervals.append((start_time, duration, current_proc))
            start_time = t
            current_proc = schedule[t]
            
    if sorted_times:
        t = sorted_times[-1] + 1
        duration = t - start_time
        if duration > 0:
            intervals.append((start_time, duration, current_proc))
            
    return intervals

def generate_gantt_chart(input_file, log_file, out_img):
    """
    Generate a single Gantt chart.
    """
    num_cpus = parse_input(input_file)
    print(f"[INFO] {os.path.basename(log_file)}: Hệ thống được cấu hình với {num_cpus} CPU.")
    
    cpu_schedule = parse_log(log_file, num_cpus)
    
    max_time = 0
    for schedule in cpu_schedule.values():
        if schedule:
            max_time = max(max_time, max(schedule.keys()))
    max_time += 1
    
    cpu_intervals = {}
    for cpu, schedule in cpu_schedule.items():
        cpu_intervals[cpu] = merge_schedule(schedule)
    
    process_colors = {
        1: '#fbb4ae', # Pink
        10: '#FFB7B2', # Light Pink/Peach
        3: '#FFDAC1', # Peach
        9: '#E2F0CB', # Light Green
        5: '#B5EAD7', # Mint Green
        6: '#C7CEEA', # Periwinkle/Blue
        7: '#e5d8bd', # Lặp lại từ đầu
        8: '#b3cde3', 
        2: '#ffffcc', 
        4: '#ccebc5',
        None: '#E5E4E2' # Light Gray cho CPU trống
    }
    # -----------------------------------------------
    
    width = max(12, max_time * 0.3)
    fig, ax = plt.subplots(figsize=(width, max(4, num_cpus * 2)))   
    row_height = 4
    row_gap = 6
    yticks = []
    y_labels = []
    
    for cpu, intervals in cpu_intervals.items():
        y = cpu * row_gap
        yticks.append(y + row_height / 2)
        y_labels.append(f"CPU {cpu}") 
        
        for (start, duration, proc) in intervals:
            color = process_colors.get(proc, '#E5E4E2') if proc is not None else '#E5E4E2'
            ax.broken_barh([(start, duration)], (y, row_height),
                           facecolors=color, edgecolor='black', linewidth=0.8)
            
            if proc is not None:
                # Giữ nguyên chữ màu đen để dễ đọc trên nền sáng
                ax.text(start + duration/2, y + row_height/2, f"P{proc}",
                        ha='center', va='center', color='black', fontsize=15)
                
    # Đặt tick (số) thẳng hàng với ranh giới của các time slot
    ax.set_xticks(range(max_time + 1))
    ax.set_xticklabels([str(x) for x in range(max_time + 1)])
    
    # Ẩn các dấu gạch dọc nhô ra ở trục X
    ax.tick_params(axis='x', which='both', length=0)
    
    # Bật lưới gióng nét đứt tại các ranh giới (ticks chính)
    ax.grid(axis='x', linestyle='--', color='gray', alpha=0.5)
    
    ax.set_xlabel("Time Slot")
    ax.set_yticks(yticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlim(0, max_time)
    
    os.makedirs(os.path.dirname(out_img) if os.path.dirname(out_img) else '.', exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_img, dpi=300)
    plt.close()
    print(f"[SUCCESS] Đã xuất biểu đồ ra file: {out_img}")

def main():
    if len(sys.argv) == 4:
        # Single chart mode
        input_file = sys.argv[1]
        log_file = sys.argv[2]
        out_img = sys.argv[3]
        generate_gantt_chart(input_file, log_file, out_img)
    elif len(sys.argv) == 1:
        # Batch mode: generate for all outputs
        input_dir = "input"
        output_dir = "run_outputs"
        charts_dir = "gantt_charts"
        
        os.makedirs(charts_dir, exist_ok=True)
        
        # Get all config files from input directory
        config_files = []
        for f in os.listdir(input_dir):
            input_path = os.path.join(input_dir, f)
            if os.path.isfile(input_path):
                config_files.append(f)
        
        config_files.sort()
        
        print("=" * 60)
        print("Generating Gantt charts for all run outputs...")
        print("=" * 60)
        
        for config_name in config_files:
            input_path = os.path.join(input_dir, config_name)
            output_path = os.path.join(output_dir, f"{config_name}.txt")
            
            if os.path.exists(output_path):
                chart_name = config_name
                output_chart = os.path.join(charts_dir, f"{chart_name}.png")
                try:
                    generate_gantt_chart(input_path, output_path, output_chart)
                except Exception as e:
                    print(f"[ERROR] Failed to generate chart for {config_name}: {e}")
            else:
                print(f"[SKIP] Output file not found: {output_path}")
        
        print("=" * 60)
        print(f"All charts have been saved to: {charts_dir}/")
        print("=" * 60)
    else:
        print("Usage:")
        print("  Single chart:  python gantt.py <input_file> <log_file> <output_image>")
        print("  Batch mode:    python gantt.py")
        sys.exit(1)

if __name__ == '__main__':
    main()
