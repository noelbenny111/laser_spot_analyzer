"""
Comprehensive test script for core.interaction module.
Tests all functionalities of ManualReviewInterface and manual_select function.

Run from project root:
    python test_interaction.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt
from unittest.mock import Mock, patch, MagicMock

from core.interaction import ManualReviewInterface, manual_select


class TestManualReviewInterface:
    """Test suite for ManualReviewInterface class."""
    
    @staticmethod
    def create_test_image(shape=(100, 100)):
        """Create a simple test image."""
        return np.random.randint(0, 255, shape, dtype=np.uint8)
    
    @staticmethod
    def create_test_blobs(count=3):
        """Create test blob data."""
        blobs = []
        for i in range(count):
            if i % 2 == 0:
                # Blob with ellipse
                blobs.append({
                    "center": (20 + i*20, 30),
                    "diam_px": 15,
                    "ellipse": ((20 + i*20, 30), (20, 10), 45)
                })
            else:
                # Blob without ellipse (circle only)
                blobs.append({
                    "center": (20 + i*20, 30),
                    "diam_px": 15,
                    "ellipse": None
                })
        return blobs
    
    def test_initialization(self):
        """Test ManualReviewInterface initialization."""
        print("\n[TEST] Testing ManualReviewInterface initialization...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        
        assert interface.img is img, "Image not stored correctly"
        assert interface.blobs == blobs, "Blobs not stored correctly"
        assert len(interface.selected) == len(blobs), "Selection list size mismatch"
        assert all(interface.selected), "Not all blobs selected by default"
        assert len(interface.patches) == len(blobs), "Patch count mismatch"
        assert not interface.finished, "Should not be finished initially"
        
        plt.close(interface.fig)
        print("✓ Initialization test passed")
    
    def test_empty_blobs(self):
        """Test with empty blob list."""
        print("\n[TEST] Testing with empty blob list...")
        img = self.create_test_image()
        blobs = []
        
        interface = ManualReviewInterface(img, blobs)
        
        assert interface.blobs == [], "Empty blobs not handled"
        assert interface.patches == [], "No patches should be created"
        
        plt.close(interface.fig)
        print("✓ Empty blobs test passed")
    
    def test_update_patch_color(self):
        """Test patch color update functionality."""
        print("\n[TEST] Testing patch color update...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(2)
        
        interface = ManualReviewInterface(img, blobs)
        
        # Test changing color for selected blob
        interface.selected[0] = True
        interface._update_patch_color(0)
        
        # Test changing color for unselected blob
        interface.selected[0] = False
        interface._update_patch_color(0)
        
        plt.close(interface.fig)
        print("✓ Patch color update test passed")
    
    def test_update_title(self):
        """Test title update with selection info."""
        print("\n[TEST] Testing title update...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        interface._update_title()
        
        title = interface.ax.get_title()
        assert "3/3" in title, "Title should show selection count"
        assert "Manual Review" in title, "Title should contain 'Manual Review'"
        
        # Deselect some and update
        interface.selected[0] = False
        interface.selected[1] = False
        interface._update_title()
        
        title = interface.ax.get_title()
        assert "1/3" in title, "Title should update with new selection count"
        
        plt.close(interface.fig)
        print("✓ Title update test passed")
    
    def test_key_press_select_all(self):
        """Test 'A' key to select all blobs."""
        print("\n[TEST] Testing 'A' key (select all)...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        interface.selected = [False, False, False]  # Start with none selected
        
        # Simulate 'A' key press
        mock_event = Mock()
        mock_event.key = 'a'
        interface._on_key_press(mock_event)
        
        assert all(interface.selected), "All blobs should be selected after 'A' key"
        
        plt.close(interface.fig)
        print("✓ Select all test passed")
    
    def test_key_press_deselect_all(self):
        """Test 'D' key to deselect all blobs."""
        print("\n[TEST] Testing 'D' key (deselect all)...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        assert all(interface.selected), "All should be selected initially"
        
        # Simulate 'D' key press
        mock_event = Mock()
        mock_event.key = 'd'
        interface._on_key_press(mock_event)
        
        assert not any(interface.selected), "No blobs should be selected after 'D' key"
        
        plt.close(interface.fig)
        print("✓ Deselect all test passed")
    
    def test_key_press_escape(self):
        """Test 'Escape' key to cancel review."""
        print("\n[TEST] Testing 'Escape' key (cancel)...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        interface.selected = [False, False, False]  # Deselect all
        interface.finished = True
        
        # Simulate Escape key press
        mock_event = Mock()
        mock_event.key = 'escape'
        interface._on_key_press(mock_event)
        
        assert all(interface.selected), "All blobs should be selected after escape"
        assert interface.finished == False, "Should not be finished (cancelled)"
        
        plt.close(interface.fig)
        print("✓ Escape key test passed")
    
    def test_key_press_enter(self):
        """Test 'Enter' key to accept selections."""
        print("\n[TEST] Testing 'Enter' key (accept)...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        interface.selected = [True, False, True]
        
        # Simulate Enter key press
        mock_event = Mock()
        mock_event.key = 'enter'
        interface._on_key_press(mock_event)
        
        assert interface.finished == True, "Should be finished after enter"
        
        plt.close(interface.fig)
        print("✓ Enter key test passed")
    
    def test_click_event_toggle(self):
        """Test mouse click to toggle blob selection."""
        print("\n[TEST] Testing click event toggle...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(2)
        
        interface = ManualReviewInterface(img, blobs)
        original_state = interface.selected[0]
        
        # Mock click event on first patch
        mock_event = Mock()
        mock_event.inaxes = interface.ax
        mock_event.xdata = 20
        mock_event.ydata = 30
        
        # Mock patch.contains to return True for first patch
        interface.patches[0].contains = Mock(return_value=(True,))
        
        interface._on_click(mock_event)
        
        assert interface.selected[0] != original_state, "Selection should be toggled"
        
        plt.close(interface.fig)
        print("✓ Click toggle test passed")
    
    def test_click_event_outside_axes(self):
        """Test click event outside plotting axes."""
        print("\n[TEST] Testing click outside axes...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(2)
        
        interface = ManualReviewInterface(img, blobs)
        original_state = interface.selected[:]
        
        # Mock click event outside axes
        mock_event = Mock()
        mock_event.inaxes = None
        
        interface._on_click(mock_event)
        
        assert interface.selected == original_state, "Selection should not change"
        
        plt.close(interface.fig)
        print("✓ Click outside axes test passed")
    
    def test_run_returns_selected_blobs(self):
        """Test that run() returns only selected blobs."""
        print("\n[TEST] Testing run() return value...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        interface = ManualReviewInterface(img, blobs)
        interface.selected = [True, False, True]
        interface.finished = True  # Set to finished to avoid blocking
        
        with patch('matplotlib.pyplot.show'):
            with patch('matplotlib.pyplot.fignum_exists', return_value=False):
                selected_blobs = interface.run()
        
        assert len(selected_blobs) == 2, "Should return 2 selected blobs"
        assert selected_blobs[0] == blobs[0], "First selected blob mismatch"
        assert selected_blobs[1] == blobs[2], "Second selected blob mismatch"
        
        plt.close(interface.fig)
        print("✓ Run return value test passed")


class TestManualSelectFunction:
    """Test suite for manual_select function."""
    
    @staticmethod
    def create_test_image(shape=(100, 100)):
        """Create a simple test image."""
        return np.random.randint(0, 255, shape, dtype=np.uint8)
    
    @staticmethod
    def create_test_blobs(count=3):
        """Create test blob data."""
        return [
            {
                "center": (20 + i*20, 30),
                "diam_px": 15,
                "ellipse": ((20 + i*20, 30), (20, 10), 45) if i % 2 == 0 else None
            }
            for i in range(count)
        ]
    
    def test_manual_select_with_empty_blobs(self):
        """Test manual_select with no blobs."""
        print("\n[TEST] Testing manual_select with empty blobs...")
        img = self.create_test_image()
        blobs = []
        
        result = manual_select(img, blobs)
        
        assert result == [], "Should return empty list for empty input"
        print("✓ Empty blobs test passed")
    
    def test_manual_select_returns_blobs(self):
        """Test that manual_select returns selected blobs."""
        print("\n[TEST] Testing manual_select return value...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(3)
        
        with patch('core.interaction.ManualReviewInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface.run.return_value = [blobs[0], blobs[2]]
            mock_interface_class.return_value = mock_interface
            
            result = manual_select(img, blobs)
        
        assert len(result) == 2, "Should return 2 blobs"
        assert result == [blobs[0], blobs[2]], "Should return selected blobs"
        print("✓ Return value test passed")
    
    def test_manual_select_calls_interface(self):
        """Test that manual_select creates and runs interface."""
        print("\n[TEST] Testing manual_select interface creation...")
        img = self.create_test_image()
        blobs = self.create_test_blobs(2)
        
        with patch('core.interaction.ManualReviewInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface.run.return_value = blobs
            mock_interface_class.return_value = mock_interface
            
            manual_select(img, blobs)
        
        mock_interface_class.assert_called_once_with(img, blobs)
        mock_interface.run.assert_called_once()
        print("✓ Interface creation test passed")


def run_all_tests():
    """Run all test cases."""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUITE FOR core.interaction")
    print("="*60)
    
    # Test ManualReviewInterface
    test_interface = TestManualReviewInterface()
    test_interface.test_initialization()
    test_interface.test_empty_blobs()
    test_interface.test_update_patch_color()
    test_interface.test_update_title()
    test_interface.test_key_press_select_all()
    test_interface.test_key_press_deselect_all()
    test_interface.test_key_press_escape()
    test_interface.test_key_press_enter()
    test_interface.test_click_event_toggle()
    test_interface.test_click_event_outside_axes()
    test_interface.test_run_returns_selected_blobs()
    
    # Test manual_select function
    test_function = TestManualSelectFunction()
    test_function.test_manual_select_with_empty_blobs()
    test_function.test_manual_select_returns_blobs()
    test_function.test_manual_select_calls_interface()
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()