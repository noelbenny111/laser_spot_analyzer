import matplotlib
matplotlib.use('Qt5Agg')  # Use Qt5 backend for compatibility with PySide6
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Circle
import matplotlib.patches as mpatches

class ManualReviewInterface:
    """Interactive manual review interface for blob selection."""
    
    def __init__(self, img, blobs):
        self.img = img
        self.blobs = blobs
        self.selected = [True] * len(blobs)
        self.patches = []
        self.current_highlight = None
        self.finished = False
        
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        plt.subplots_adjust(bottom=0.15)
        
        # Display image
        self.ax.imshow(self.img, cmap="gray")
        
        # Create patches for all blobs
        for i, b in enumerate(blobs):
            if b["ellipse"]:
                p = Ellipse(b["ellipse"][0], *b["ellipse"][1], angle=b["ellipse"][2],
                            edgecolor="lime", facecolor="none", linewidth=2)
            else:
                p = Circle(b["center"], b["diam_px"] / 2,
                           edgecolor="lime", facecolor="none", linewidth=2)
            self.ax.add_patch(p)
            self.patches.append(p)
        
        self._update_title()
        
        # Add legend
        wanted = mpatches.Patch(color='lime', label='Wanted (Selected)')
        unwanted = mpatches.Patch(color='red', label='Unwanted (Rejected)')
        self.ax.legend(handles=[wanted, unwanted], loc='upper right', fontsize=10)
        
        # Connect events
        self.fig.canvas.mpl_connect("button_press_event", self._on_click)
        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        
    def _update_title(self):
        """Update title with current selection info."""
        selected_count = sum(self.selected)
        total_count = len(self.blobs)
        title = (f"Manual Review: {selected_count}/{total_count} selected | "
                f"Click blob to toggle | Keys: A=SelectAll, D=DeselectAll, Enter=Accept, Esc=Cancel")
        self.ax.set_title(title, fontsize=11, pad=10)
    
    def _on_click(self, event):
        """Handle mouse click on blobs."""
        if event.inaxes != self.ax or event.xdata is None:
            return
        
        # Check which patch was clicked
        for i, p in enumerate(self.patches):
            if p.contains(event)[0]:
                # Toggle selection
                self.selected[i] = not self.selected[i]
                self._update_patch_color(i)
                self._update_title()
                self.fig.canvas.draw_idle()
                break
    
    def _update_patch_color(self, index):
        """Update patch color based on selection state."""
        color = "lime" if self.selected[index] else "red"
        self.patches[index].set_edgecolor(color)
    
    def _on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.key == 'a':  # Select all
            self.selected = [True] * len(self.blobs)
            for i in range(len(self.patches)):
                self._update_patch_color(i)
            self._update_title()
            self.fig.canvas.draw_idle()
            print("[REVIEW] Selected ALL blobs")
        
        elif event.key == 'd':  # Deselect all
            self.selected = [False] * len(self.blobs)
            for i in range(len(self.patches)):
                self._update_patch_color(i)
            self._update_title()
            self.fig.canvas.draw_idle()
            print("[REVIEW] Deselected ALL blobs")
        
        elif event.key == 'enter':  # Accept and finish
            self.finished = True
            plt.close(self.fig)
            print(f"[REVIEW] Accepting {sum(self.selected)}/{len(self.blobs)} blobs")
        
        elif event.key == 'escape':  # Cancel
            self.selected = [True] * len(self.blobs)
            self.finished = False
            plt.close(self.fig)
            print("[REVIEW] Review cancelled - all blobs kept")
    
    def run(self):
        """Display the review interface and return selected blobs."""
        print("[REVIEW] Showing review interface (non-blocking)...")
        
        # Show window non-blocking (compatible with Qt event loop)
        plt.show(block=False)
        
        # Process events until user finishes
        while not self.finished and plt.fignum_exists(self.fig.number):
            plt.pause(0.1)  # Small pause to prevent CPU spinning
        
        # Final pause to ensure all events processed
        plt.pause(0.2)
        
        # Return selected blobs
        selected_blobs = [b for i, b in enumerate(self.blobs) if self.selected[i]]
        print(f"[REVIEW] Completed: {len(selected_blobs)}/{len(self.blobs)} blobs selected")
        return selected_blobs


def manual_select(img, blobs):
    """Interactive manual review of detected blobs."""
    if not blobs:
        print("[REVIEW] No blobs to review")
        return blobs
    
    print(f"\n[REVIEW] Opening manual review interface for {len(blobs)} blobs...")
    print("[REVIEW] Instructions:")
    print("  - Click on blobs to toggle selection (Green=wanted, Red=unwanted)")
    print("  - Press 'A' to select all blobs")
    print("  - Press 'D' to deselect all blobs")
    print("  - Press 'Enter' to accept selections and continue")
    print("  - Press 'Esc' to cancel and keep all blobs")
    
    reviewer = ManualReviewInterface(img, blobs)
    selected_blobs = reviewer.run()
    
    return selected_blobs
