""""GUI for NSIHDR conversion tool"""

import logging
import os
import tkinter as tk
from enum import Enum
from importlib.metadata import version
from pprint import pformat
from tkinter import (E, N, S, StringVar, Toplevel, W, filedialog, ttk)

from rawtools import nsihdr
from ttkthemes import ThemedTk

__version__ = version('rawtools')

class GuiState(Enum):
	IDLE = 1
	PROCESSING = 2
	ERROR = 3

def center(root, toplevel):
	toplevel.update_idletasks()

	# Tkinter way to find the screen resolution
	# screen_width = toplevel.winfo_screenwidth()
	# screen_height = toplevel.winfo_screenheight()

	# PyQt way to find the screen resolution
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()

	size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
	x = screen_width/2 - size[0]/2
	y = screen_height/2 - size[1]/2

	toplevel.geometry("+%d+%d" % (x, y))

class App():
	def __init__(self, args):
		self.source = 'C:/Users/Tim Parker/Datasets/topp/xrt/development/batch-export'
		self.args = args
		# Source: https://www.elegantthemes.com/blog/freebie-of-the-week/beautiful-flat-icons-for-free
		self.icon_fp = "rawtools\\assets\\tools.ico"
		self.icon_caution_fp = "rawtools\\assets\\caution.ico"
		self.state = GuiState.IDLE


		self.root = ThemedTk(theme='arc')
		root = self.root
		root.title(f"Batch Export Tool v{__version__}")
		root.resizable(False, False)
		menubar = tk.Menu(root)

		file_menu = tk.Menu(menubar, tearoff=False)
		file_menu.add_command(label="View Logs", command=lambda: print("Load logs"))
		file_menu.add_separator()
		file_menu.add_command(label="Quit", command=self.quitApplication, accelerator='Ctrl-Q')
		menubar.add_cascade(label="File", menu=file_menu)

		help_menu = tk.Menu(menubar, tearoff=False)
		help_menu.add_command(label="About", command = None)
		help_menu.add_separator()
		help_menu.add_command(label="Documentation")
		menubar.add_cascade(label="Help", menu=help_menu)
		root.config(menu = menubar)

		# Assign hotkey(s)
		root.bind("<Control-q>", self.quitApplication)

		mainframe = ttk.Frame(root, padding="16 16")
		mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
		self.mainframe = mainframe

		root.iconbitmap(self.icon_fp)

		# Source folder selection
		src_intro_label_text = "Select an NSI Reconstruction folder."
		src_intro_label = ttk.Label(mainframe, text=src_intro_label_text)
		src_intro_label.grid(row=0, column=0, sticky=(E,W), pady="0 8")

		self.src = tk.StringVar()
		self.src.set(self.source)
		# # Add event handling to changes to the source directory text field
		self.src_entry = ttk.Entry(mainframe, textvariable = self.src, width=85)
		self.src_entry.grid(row=1, column=0, columnspan=3, sticky=(E, W), padx="0 8", pady="0 16")

		self.src_folder_btn = ttk.Button(mainframe, text = 'Select Folder', command=self.choose_src)
		self.src_folder_btn.grid(row=1, column=4, columnspan=1, pady="0 16", padx="8 0")

		# Export data
		self.export_btn = ttk.Button(mainframe, text = 'Export', command=self.export)
		self.export_btn.grid(row=2, column=0, columnspan=5, pady="0 8")

		# Center window on screen
		root.update() # virtual pre-render of GUI to calculate actual sizes
		w = root.winfo_reqwidth()
		h = root.winfo_reqheight()
		logging.debug(f"Root width: {w}")
		logging.debug(f"Root height: {h}")
		ws = root.winfo_screenwidth()
		hs = root.winfo_screenheight()
		# calculate position x, y
		x = (ws/2) - (w/2)    
		y = (hs/2) - (h/2)
		root.geometry('+%d+%d' % (x, y))

		# Display window to user
		root.mainloop()

	def choose_src(self):
		"""Select a folder to act as data source"""
		self.source = filedialog.askdirectory(initialdir=self.source, title="Choose directory")
		logging.debug(f'Selected folder: {self.source}')
		self.src.set(self.source)

	def scan_folder(self, path):
		"""Scan folder for nsihdr and corresponding raw files

		Args:

			path (str): Input path
		"""
		logging.debug(f"{path=}")
		if len(path) < 2:
			return

		# Invalid path provided, abort
		if not (os.path.exists(path) and os.path.isdir(path)):
			return

		# Get all files
		files = [ files for r, d, files in os.walk(path) ][0]
		logging.debug(f"{files=}")

		# Filter NSIHDR files
		nsihdr_files = [ f for f in files if f.endswith('.nsihdr') ]
		logging.debug(f"{nsihdr_files=}")

		# Filter RAW files
		raw_files = [ f for f in files if f.endswith('.raw') ]
		logging.debug(f"{raw_files=}")

		# Determine what RAW would be created from the NSIHDR files
		expected_raw_files = [ '.'.join([os.path.splitext(f)[0], 'raw']) for f in nsihdr_files ]
		logging.debug(f"{expected_raw_files=}")


		# # Get all files
		logging.debug(f"All input scans: {nsihdr_files}")
		nsihdr_files = list(set(nsihdr_files)) # remove duplicates
		logging.debug(f"Unique input scans: {nsihdr_files}")

		return nsihdr_files, raw_files, expected_raw_files

	def export(self):
		# Get selected path
		path = self.src.get()
		self.args.path = [path] # CLI requires list of paths
		self.cancelled = False

		# Scan input directory for .NSIHDR files
		nsihdr_files, raw_files, expected_raw_files = self.scan_folder(path)

		# Prompt user with actions
		# Case 1: Existing data
		overlapping_raw_files = list(set(raw_files) & set(expected_raw_files))
		logging.debug(f"{overlapping_raw_files=}")
		if len(overlapping_raw_files) > 0:
			prompt_title = "Warning - File Conflict Encountered"
			at_risk_files = '\n'.join(overlapping_raw_files)
			if len(overlapping_raw_files) == 1:
				prompt_message = "A conflict in the data files was encountered.\n\nThe following reconstructed volume appears to have already been exported.\n\n"+at_risk_files+"\n\nDo you want to overwrite this file? This will first *destroy* it."
			else:
				prompt_message = "A conflict in the data files was encountered.\n\nThe following reconstructed volumes appear to have already been exported.\n\n"+at_risk_files+"\n\nDo you want to overwrite these files? This will first *destroy* them."
			logging.warning(prompt_message)

			self.prompt = Toplevel(self.root)
			self.prompt.title(prompt_title)
			self.prompt.iconbitmap(self.icon_caution_fp)
			self.prompt.resizable(False, False)
			self.prompt_frame = ttk.Frame(self.prompt, padding="16 16")
			self.prompt_frame.grid(column=0, row=0, sticky=(N, S, E, W))
			self.prompt_message = ttk.Label(self.prompt_frame, text=prompt_message).grid(row = 0, column = 0, columnspan=3, pady="0 32")
			self.prompt_button = ttk.Button(self.prompt_frame, text="Overwrite", command=self.overwrite_files).grid(row = 1, column = 0, columnspan=1)
			self.prompt_button = ttk.Button(self.prompt_frame, text="Skip", command=self.skip_files).grid(row = 1, column = 1, columnspan=1)
			self.prompt_button = ttk.Button(self.prompt_frame, text="Cancel", command=self.cancel_export).grid(row = 1, column = 2, columnspan=1)

			# Orient window on screen
			center(self.root, self.prompt)
			# Disable interaction with parent window
			self.prompt.protocol("WM_DELETE_WINDOW", self.dismiss)
			self.prompt.transient(self.root)
			self.prompt.wait_visibility()
			self.prompt.grab_set()
			self.prompt.wait_window()

		# Only new data was found
		else:
		# Case 2: New data
			prompt_title = "Confirm Action - Export"
			expected_raw_files = '\n'.join(expected_raw_files)
			if len(overlapping_raw_files) == 1:
				prompt_message = "The following file will be generated.\n\n"+expected_raw_files
			else:
				prompt_message = "The following files will be generated.\n\n"+expected_raw_files
			logging.debug(prompt_message)

			self.prompt = Toplevel(self.root)
			self.prompt.title(prompt_title)
			self.prompt.iconbitmap(self.icon_fp)
			self.prompt.resizable(False, False)
			self.prompt_frame = ttk.Frame(self.prompt, padding="16 16")
			self.prompt_frame.grid(column=0, row=0, sticky=(N, S, E, W))
			self.prompt_message = ttk.Label(self.prompt_frame, text=prompt_message).grid(row = 0, column = 0, columnspan=4, pady="0 32")
			self.prompt_button = ttk.Button(self.prompt_frame, text="Ok", command=self.dismiss).grid(row = 1, column = 1, columnspan=1)
			self.prompt_button = ttk.Button(self.prompt_frame, text="Cancel", command=self.cancel_export).grid(row = 1, column = 2, columnspan=1)

			# Orient window on screen
			center(self.root, self.prompt)
			# Disable interaction with parent window
			self.prompt.protocol("WM_DELETE_WINDOW", self.dismiss)
			self.prompt.transient(self.root)
			self.prompt.wait_visibility()
			self.prompt.grab_set()
			self.prompt.wait_window()

		# Process data
		if not self.cancelled:
			# Do processing
			logging.debug(self.args)
			self.args.gui_window = self.root
			nsihdr.main(self.args)
		else:
			logging.debug(f"Cancelled export")

	def quitApplication(self, _event=None):
		self.root.destroy()

	def overwrite_files(self):
		# Case 1a: Overwrite all data and create new
		self.args.force = True
		self.dismiss()

	def skip_files(self):
		# Case 1b: Skip all existing data
		self.args.force = False # just in case it was enabled via CLI
		self.dismiss()

	def cancel_export(self):
		# Case 1b: Skip all existing data
		self.cancelled = True
		self.dismiss()

	def dismiss(self):
		self.prompt.grab_release()
		self.prompt.destroy()
