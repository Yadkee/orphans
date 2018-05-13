#! python3
import tkinter as tk


def userAndTag(user, tag):
    return user.decode() + "#" + tag.hex()


class Hub(tk.Frame):
    def __init__(self, master, client, tagStr):
        def update():
            tags = client.tags
            queue = client.queue
            queueFlags = client.queueFlags
            lt, lq, lqf = self.last
            if lt != tags:
                self.usersList.delete(0, "end")
                self.usersList.insert("end", *(userAndTag(users[tag], tag)
                                               for tag in sorted(tags)))
            if lq != queue or lqf != queueFlags:
                self.queueList.delete(0, "end")
                iterable = (userAndTag(users[tag], tag) +
                            client.queueFlags[tag].decode()
                            for tag in sorted(queue))
                self.queueList.insert(0, *iterable)
            self.last = (tags.copy(), queue.copy(), queueFlags.copy())
        tk.Frame.__init__(self, master)
        master.minsize(600, 400)
        client.update = update
        users = client.users
        self.client = client
        self.last = (None, None, None)

        self.serverLabel = tk.Label(self, text=client.server[0],
                                    font=("Times", 50, "bold"))
        self.clientLabel = tk.Label(self, text=tagStr,
                                    font=("Times", 30), fg="gray")
        self.queueList = tk.Listbox(self)
        self.usersList = tk.Listbox(self)
        self.configLabel = tk.Label(self, text="CONFIG:")
        # TODO: configFrame containing all the config options
        self.button = tk.Button(self, text="PLAY")
        # TODO: Redesign all the widgets and organization

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        self.serverLabel.grid(column=0, row=0, columnspan=2, sticky="W")
        self.clientLabel.grid(column=2, row=0, sticky="E")
        self.queueList.grid(column=0, row=1, rowspan=2, sticky="NSEW")
        self.usersList.grid(column=2, row=1, rowspan=2, sticky="NSEW")
        self.configLabel.grid(column=1, row=1, sticky="NSEW")
        self.button.grid(column=1, row=2, sticky="SEW")

    def close(self):
        self.grid_forget()
        self.client.update = lambda: None
