import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import ast
import os

SETTINGS_FILE = "recent_settings.txt"
DEFAULT_SETTINGS = {
	"stag_libraries": [17, 19, 21 ,23],
	"input_resolution_factor": 1,
	"output_zoom": 1.0,
	"normalise_view": False,
	"SHUTTERUS": 3000,
	"GAIN": 15,
	"n_cols": 21,
	"save_video": False,
	"filename_addon": ""
}

#input resolution
RES_OPTIONS = {
	"1 (760x1014)": 1,
	"2 (1520x2028)": 2,
	"3 (2280x3042)": 3,
	"4 (3040x4056)": 4
}
inv_RES_OPTIONS = {v: k for k, v in RES_OPTIONS.items()}


    
def load_settings():
	if os.path.exists(SETTINGS_FILE):
		try:
			with open(SETTINGS_FILE, "r") as f:
				contents = f.read()
				return ast.literal_eval(contents)
		except Exception as e:
			print("Error loading settings", e)
	return DEFAULT_SETTINGS.copy()

def save_settings(settings):
	with open(SETTINGS_FILE, "w") as f:
		f.write(str(settings))

class STag_GUI:
	def __init__(self, root):
		self.root= root
		self.root.title("real-time-tag-detector")
		
		self.settings = load_settings()
		self.vars = {}
		
		self.create_widgets()
		self.started = False #a flag to track whether 'start' was clicked
	
	def create_widgets(self):
		'''
		first box - processing settings
		'''
		top_frame = ttk.LabelFrame(self.root, text="STag detection settings")
		top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

		# === Column 0: STag Libraries ===
		ttk.Label(top_frame, text="STag Libraries (multi-select):").grid(row=0, column=0, sticky="w", pady=(5, 2))

		# Subframe for vertical toggle layout
		stag_frame = ttk.Frame(top_frame)
		stag_frame.grid(row=1, column=0, rowspan=4, sticky="nw", pady=(0, 5))

		self.stag_vars = {}
		for i, val in enumerate([17, 19, 21, 23]):
			var = ttk.BooleanVar(value=val in self.settings["stag_libraries"])
			self.stag_vars[val] = var
			ttk.Checkbutton(
				stag_frame,
				text=str(val),
				variable=var,
				bootstyle="success,round-toggle"
			).grid(row=i, column=0, sticky="w", pady=2)

		# === Column 1: n_cols label, spinbox and description ===
		self.vars["n_cols"] = ttk.IntVar(value=self.settings["n_cols"])
		ttk.Label(top_frame, text="Track how many recent tags? (1–21):").grid(
			row=0, column=1, sticky="w", padx=(20, 5), pady=(5, 2)
		)

		ttk.Spinbox(
			top_frame,
			from_=1,
			to=21,
			textvariable=self.vars["n_cols"],
			bootstyle="success",
			width=5
		).grid(row=1, column=1, sticky="w", padx=(20, 5), pady=(0, 2))

		ttk.Label(
			top_frame,
			text="Set to 1 to detect tags only. Higher values show coloured tracks of the last N detections.",
			wraplength=220
		).grid(row=2, column=1, columnspan=1, sticky="w", padx=(20, 5), pady=(0, 10))

		# === Column 2: Normalise brightness ===
		self.vars["normalise_view"] = ttk.BooleanVar(value=self.settings["normalise_view"])
		ttk.Checkbutton(
			top_frame,
			text="Normalise Brightness?",
			variable=self.vars["normalise_view"],
			bootstyle="success,round-toggle"
		).grid(row=0, column=2, sticky="w", padx=10)

		ttk.Label(
			top_frame,
			text="(Not recommended. Can improve contrast at the expense of increased false positives. Try increasing GAIN first)",
			wraplength=220
		).grid(row=1, column=2, sticky="w", padx=10, pady=(0, 10))

		# Improve resizing behavior
		for i in range(3):
			top_frame.columnconfigure(i, weight=1)
		'''
		Left box - Camera
		'''
		cam_frame = ttk.Labelframe(self.root, text="Camera Settings")
		cam_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
		
		#Shutter speed (microseconds)
		self.vars["SHUTTERUS"] = ttk.IntVar(value=self.settings["SHUTTERUS"])
		ttk.Label(cam_frame, text="Shutter speed, microseconds (1-120000):").grid(row=0, column=0, sticky="w")
		ttk.Entry(cam_frame, textvariable=self.vars["SHUTTERUS"], bootstyle="success").grid(row=0, column=1)
		
		self.vars["GAIN"] = ttk.IntVar(value=self.settings["GAIN"])
		ttk.Label(cam_frame, text="GAIN - brightens the image (≥0):").grid(row=1, column=0, sticky="w")
		ttk.Entry(cam_frame, textvariable=self.vars["GAIN"], bootstyle="success").grid(row=1, column=1)
		
		

		self.vars["input_resolution_factor_str"] = ttk.StringVar(
			value=inv_RES_OPTIONS.get(self.settings["input_resolution_factor"], "1 (760x1014)")
		)

		ttk.Label(cam_frame, text="Input Resolution (higher res. = better detection but slower framerate):").grid(row=3, column=0, sticky="w")
		ttk.OptionMenu(cam_frame, self.vars["input_resolution_factor_str"], 
			self.vars["input_resolution_factor_str"].get(), *RES_OPTIONS.keys(), bootstyle="success").grid(row=3, column=1)
		
		#output zoom
		self.vars["output_zoom"] = ttk.DoubleVar(value=self.settings["output_zoom"])
		ttk.Label(cam_frame, text="Virtual zoom (1.0–10.0):").grid(row=2, column=0, sticky="w")
		ttk.Entry(cam_frame, textvariable=self.vars["output_zoom"], bootstyle="success").grid(row=2, column=1)
		
		'''
		Right box - output
		'''
		# Right box – Output
		out_frame = ttk.Labelframe(self.root, text="Output Settings")
		out_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
		
		self.vars["save_video"] = ttk.BooleanVar(value=self.settings["save_video"])
		ttk.Checkbutton(
			out_frame,
			text="Save video?",
			variable=self.vars["save_video"],
			bootstyle="success,round-toggle"
		).grid(row=1, column=0, pady=10, sticky="w")

		self.vars["filename_addon"] = ttk.StringVar(value=self.settings.get("filename_addon", ""))
		ttk.Label(out_frame, text="saved video Filename Addon (optional):").grid(row=3, column=0, pady=10, sticky="w")
		ttk.Entry(out_frame, textvariable=self.vars["filename_addon"], bootstyle="success").grid(row=4, column=0)

		'''
		Bottom – Start Button
		'''
		start_btn = ttk.Button(self.root, text="Start", command=self.on_start, bootstyle="danger")
		start_btn.grid(row=2, column=0, columnspan=2, pady=10)
		
	def on_start(self):
		try:
			settings = {
				"stag_libraries": [k for k, v in self.stag_vars.items() if v.get()],
				"normalise_view": self.vars["normalise_view"].get(),
				"n_cols": int(self.vars["n_cols"].get()),
				"SHUTTERUS": int(self.vars["SHUTTERUS"].get()),
				"GAIN": int(self.vars["GAIN"].get()),
				"input_resolution_factor": RES_OPTIONS[self.vars["input_resolution_factor_str"].get()],
				"output_zoom": round(float(self.vars["output_zoom"].get()), 1),
				"save_video": self.vars["save_video"].get(),
				"filename_addon": self.vars["filename_addon"].get().strip()
			}
			# Logic link between n_cols and colour_coding
			settings["colour_coding"] = settings["n_cols"] > 1

			save_settings(settings)
			self.started=True
			self.root.destroy()  # This closes the GUI
		except Exception as e:
			messagebox.showerror("Error", f"Failed to save settings:\n{e}")
			
if __name__ == "__main__":
	root = ttk.Window
	root.style.theme_use("darkly")  # or try other themes like "darkly", "cyborg", "minty"
	app = STag_GUI(root)
	root.mainloop()

