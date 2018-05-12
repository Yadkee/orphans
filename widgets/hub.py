#! python3
import tkinter as tk


class Hub(tk.Frame):
    def __init__(self, master, client, tagStr):
        def update():
            users = client.users
            queue = client.queue
            lu, lq = self.last
            if lu != users:
                pass  # Update users list
            if lq != queue:
                pass  # Update queue list
            self.last = (users, queue)
        tk.Frame.__init__(self, master)
        master.minsize(600, 400)
        client.update = update
        self.client = client
        self.last = (None, None)

        self.serverLabel = tk.Label(self, text=client.server[0],
                                    font=("Times", 50, "bold"))
        self.clientLabel = tk.Label(self, text=tagStr,
                                    font=("Times", 30), fg="gray")
        self.button = tk.Button(self, text="PLAY")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.serverLabel.grid(column=0, row=0, columnspan=2, sticky="W")
        self.clientLabel.grid(column=2, row=0, sticky="E")
        self.button.grid(column=1, row=2, sticky="SEW")

    def close(self):
        self.grid_forget()
        self.client.update = lambda: None
