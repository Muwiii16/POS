import tkinter as tk
from core.gui import POSapp

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("400x500")
    app = POSapp(root)
    root.mainloop()
