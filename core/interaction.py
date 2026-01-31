import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle

def manual_select(img, blobs):
    fig, ax = plt.subplots()
    ax.imshow(img, cmap="gray")

    selected = [True] * len(blobs)
    patches = []

    for i, b in enumerate(blobs):
        if b["ellipse"]:
            p = Ellipse(b["ellipse"][0], *b["ellipse"][1], angle=b["ellipse"][2],
                        edgecolor="lime", facecolor="none")
        else:
            p = Circle(b["center"], b["diam_px"] / 2,
                       edgecolor="lime", facecolor="none")
        ax.add_patch(p)
        patches.append(p)

    def on_click(e):
        for i, p in enumerate(patches):
            if p.contains(e)[0]:
                selected[i] = not selected[i]
                p.set_edgecolor("lime" if selected[i] else "red")
                fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", on_click)
    plt.show()

    return [b for i, b in enumerate(blobs) if selected[i]]
