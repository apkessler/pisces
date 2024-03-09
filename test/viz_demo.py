import tkinter as tk


def read_gpios():
    try:
        with open("gpiostate.txt", "r") as file:
            lines = file.readlines()
            if lines:
                bits = lines[-1].strip().split()
                the_list = list(map(int, bits))
                if len(the_list) != 11:
                    return None
                return the_list
    except FileNotFoundError:
        print("File 'gpios.txt' not found.")
    except Exception as e:
        print(f"Error reading 'gpios.txt': {e}")
    return None


def update_circle_colors():
    bits = read_gpios()
    if bits is None:
        print("Bad read")
        return

    for i, bit in enumerate(bits):
        if bit == 1:
            gpio_indicator[i].config(bg="yellow")
        else:
            gpio_indicator[i].config(bg="gray")

    aqlights[0].config(bg="gray" if not bits[4] else "white" if bits[5] else "blue")
    aqlights[1].config(bg="gray" if not bits[6] else "white" if bits[7] else "blue")

    for i, outlet in enumerate(outlets):
        outlet.config(bg="white" if bits[i] else "gray")


def update_gpios(event=None):
    update_circle_colors()
    root.after(300, update_gpios)  # Update every 1000 milliseconds (1 second)


# Create the main window
root = tk.Tk()
root.title("GPIO Monitor")

# Create circles
gpio_indicator = [
    tk.Label(root, text=f"{i}", width=5, height=2, bg="gray", bd=2, relief="ridge")
    for i in range(11)
]

aqlights = [
    tk.Label(
        root, text=f"TankLight{i+1}", width=5, height=2, bg="gray", bd=2, relief="ridge"
    )
    for i in range(2)
]
outlets = [
    tk.Label(
        root, text=f"Outlet{i+1}", width=5, height=2, bg="gray", bd=2, relief="ridge"
    )
    for i in range(4)
]
# Arrange circles in a grid
for i, elm in enumerate(gpio_indicator + aqlights + outlets):
    row, col = divmod(i, 11)
    elm.grid(row=row, column=col, padx=5, pady=5)

# Update circle colors initially
update_circle_colors()

# Start monitoring gpios.txt
update_gpios()

# Run the Tkinter event loop
root.mainloop()
