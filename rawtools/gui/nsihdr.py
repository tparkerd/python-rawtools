""""GUI for NSIHDR conversion tool"""

import logging
import os
import tkinter as tk
from pprint import pformat
from tkinter import E, N, S, W, filedialog, ttk

from ttkthemes import ThemedTk

class App():
	def __init__(self, args):
		self.source = ''

		root = ThemedTk(theme='arc')
		root.title("Batch Export Tool - NSIHDR to RAW + DAT")
		root.resizable(False, False)
		mainframe = ttk.Frame(root, padding="16 16")
		mainframe.grid(column=0, row=0, sticky=(N, S, E, W))
		mainframe.columnconfigure(0, weight=1)

		# Source folder selection
		src_intro_label_text = "Choose a directory that contains NSIHDR."
		src_intro_label = ttk.Label(mainframe, text=src_intro_label_text)
		src_intro_label.grid(row=0, column=0, columnspan=3, sticky=(E,W), pady="0 8")

		src_label = ttk.Label(mainframe, text="Source Directory:")
		src_label.grid(row=1, column=0, sticky=W, pady="0 8")

		self.src = tk.StringVar()
		self.src.set(self.source)
		# # Add event handling to changes to the source directory text field
		self.src.trace("w", lambda value = self.src: self.scan_folder([value]))
		self.src_entry = ttk.Entry(mainframe, textvariable = self.src, width = 100)
		self.src_entry.grid(row=2, column=0, sticky=(E, W), padx="0 8", pady="0 16")

		self.src_folder_btn = ttk.Button(mainframe, text = 'Select Folder', command=self.choose_src)
		self.src_folder_btn.grid(row=2, column=1, pady="0 16", padx="8 0")

		# Export data
		self.export_btn = ttk.Button(mainframe, text = 'export', command=self.export)
		self.export_btn.grid(row=12, column=0, pady="0 8", columnspan=3)


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
		# self.files = scan_folder(path = [self.source])

	def scan_folder(path):
		# Gather all files
		logging.info(path)
		files = []
		for p in path:
			for root, _, files in os.walk(p):
				for filename in files:
					files.append(os.path.join(root, filename))
					logging.info(filename)

		# Append any loose, explicitly defined paths to .nsihdr files
		files.extend([ f for f in path if f.endswith('.nsihdr') ])

		# Filter out non-NSIHDR files
		files = [ f for f in files if f.endswith('.nsihdr') ]

		# Get all RAW files
		logging.debug(f"All files: {pformat(files)}")
		files = list(set(files)) # remove duplicates
		logging.debug(f"Unique files: {pformat(files)}")

		return files

	def export(self):
		logging.debug("PLACEHOLDER - EXPORT DATA")

